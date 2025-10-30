package collector

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"sync"
	"time"

	"github.com/dnstap/golang-dnstap"
	"google.golang.org/protobuf/proto"

	"gbenson.net/go/logger"
	"gbenson.net/hive/messaging"
)

type Service struct {
	log      *logger.Logger
	stopWait sync.WaitGroup
}

func (s *Service) Start(
	ctx context.Context,
	ch messaging.Channel,
) (<-chan error, error) {
	s.log = logger.Ctx(ctx)

	ln, err := net.Listen("tcp", ":6000")
	if err != nil {
		return nil, err
	}

	r := dnstap.NewFrameStreamSockInput(ln)
	r.SetTimeout(30 * time.Second)
	r.SetLogger(&dnstapLogger{s.log})

	dataC := make(chan []byte)
	errC := make(chan error, 1) // 2 if receiver uses it

	s.stopWait.Add(1)
	go func() {
		defer s.stopWait.Done()

		s.log.Debug().Msg("Starting sender")

		var err error
		for b := range dataC {
			if err = s.onData(ctx, ch, b); err != nil {
				break
			}
		}

		s.log.Debug().Err(err).Msg("Service.onData failed")
		errC <- err
		s.log.Debug().Err(err).Msg("Sender stopping")
	}()

	// XXX FrameStreamSockInput.ReadInto never returns
	s.log.Debug().Str("address", ln.Addr().String()).Msg("Starting receiver")
	go r.ReadInto(dataC)

	return errC, nil
}

func (s *Service) Close() error {
	return nil
}

type dnstapLogger struct {
	log *logger.Logger
}

func (d *dnstapLogger) Printf(format string, v ...interface{}) {
	d.log.Info().Msg(fmt.Sprintf(format, v...))
}

func (s *Service) onData(
	ctx context.Context,
	ch messaging.Channel,
	frame []byte,
) error {
	if err := ctx.Err(); err != nil {
		return err
	}

	var dt dnstap.Dnstap
	if err := proto.Unmarshal(frame, &dt); err != nil {
		return err
	}

	b, ok := dnstap.JSONFormat(&dt)
	if !ok {
		return errors.New("dnstap.JSONFormat failed")
	}

	s.log.Debug().RawJSON("frame", b).Msg("Received")

	var v interface{}
	if err := json.Unmarshal(b, &v); err != nil {
		return err
	}

	event := messaging.NewEvent()
	event.SetData("application/json", v)

	return ch.PublishEvent(ctx, "dnstap.events", event)
}
