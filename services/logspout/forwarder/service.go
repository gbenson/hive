package forwarder

import (
	"context"
	"encoding/json"
	"net"
	"sync"
	"sync/atomic"

	"gbenson.net/go/logger"
	"gbenson.net/hive/messaging"
)

type Service struct {
	log      *logger.Logger
	conn     atomic.Pointer[net.PacketConn]
	stopWait sync.WaitGroup
}

func (s *Service) Start(ctx context.Context, ch messaging.Channel) error {
	s.log = logger.Ctx(ctx)

	if conn, err := net.ListenPacket("udp", ":5000"); err != nil {
		return err
	} else {
		s.conn.Store(&conn)
	}

	s.stopWait.Add(1)

	go func() {
		defer s.stopWait.Done()

		s.receive(ctx, ch)
	}()

	return nil
}

func (s *Service) Close() error {
	connP := s.conn.Swap(nil)
	if connP == nil {
		return nil
	}

	logger.LoggedClose(s.log, *connP, "Receiver connection")
	s.log.Debug().Msg("Waiting for receiver to stop")
	s.stopWait.Wait()
	s.log.Debug().Msg("Receiver stopped")

	return nil
}

type record struct {
	RunID    string      `json:"run"`    // Unique UUID of this forwarder run.
	Sequence uint64      `json:"seq"`    // Order this record was received.
	Record   interface{} `json:"record"` // Received record, decoded from JSON.
}

func (s *Service) receive(ctx context.Context, ch messaging.Channel) {
	connP := s.conn.Load()
	if connP == nil {
		panic("no connection")
	}
	conn := *connP

	runID, err := randomUUID()
	if err != nil {
		s.log.Warn().Err(err).Msg("Generating run ID")
	}

	s.log.Info().
		Str("run_id", runID).
		Str("addr", conn.LocalAddr().String()).
		Msg("Receiving")

	var seq uint64
	for {
		if err := ctx.Err(); err != nil {
			s.log.Debug().Err(err).Msg("Receive")
			return
		}

		var buf [1472]byte // mtu1500-ipv4 header size
		n, _, err := conn.ReadFrom(buf[:])
		if n == 0 && ctx.Err() != nil {
			continue
		}

		go s.handle(ctx, ch, runID, seq, buf[:n], err)

		seq++
	}
}

func (s *Service) handle(
	ctx context.Context,
	ch messaging.Channel,
	runID string,
	seq uint64,
	buf []byte,
	err error,
) {
	log := s.log.With().Uint64("seq", seq).Logger()

	if err != nil {
		log.Warn().Err(err).Msg("Receive")
	}

	if len(buf) == 0 {
		return
	} else if len(buf) == cap(buf) {
		log.Warn().Msg("Possible truncation")
	}

	var v interface{}
	if err := json.Unmarshal(buf, &v); err != nil {
		log.Warn().Err(err).Msg("Malformed JSON")
		return
	}
	log.Trace().Interface("record", v).Msg("Received")

	event := messaging.NewEvent()
	event.SetData("application/json", &record{runID, seq, v})

	err = ch.PublishEvent(ctx, "logspout.events", event)
	if err != nil {
		log.Warn().Err(err).Msg("Publish")
	}
}
