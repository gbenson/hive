// hive-matrix-connector is the Matrix connector service for Hive.
package main

import (
	"context"
	"errors"
	"log"
	"sync"

	"gbenson.net/hive/matrix"
	"gbenson.net/hive/messaging"
	"gbenson.net/hive/service"

	"maunium.net/go/mautrix/event"

	"github.com/rs/zerolog"
)

func main() {
	service.Run(&Service{})
}

type Service struct {
	Log zerolog.Logger

	matrixConn   *matrix.Conn
	cancelSync   context.CancelFunc
	syncStopWait sync.WaitGroup

	cmc ChatMessageConsumer
}

func (s *Service) Start(ctx context.Context, ch *messaging.Channel) error {
	s.Log = zerolog.New(zerolog.NewConsoleWriter())

	if err := s.startMatrix(ctx); err != nil {
		return err
	}

	if err := ch.ConsumeEvents(ctx, "chat.messages", &s.cmc); err != nil {
		return err
	}

	return nil
}

func (s *Service) startMatrix(ctx context.Context) error {
	conn, err := matrix.Dial(&matrix.DialOptions{ConfigKey: "hive", Log: s.Log})
	if err != nil {
		return err
	}
	s.matrixConn = conn

	if err := conn.OnEventType(
		event.EventMessage,
		func(ctx context.Context, e *event.Event) {
			log.Println(
				"INFO: EventMessage: sender=%q type=%q id=%q body=%v",
				e.Sender.String(),
				e.Type.String(),
				e.ID.String(),
				e.Content.AsMessage().Body,
			)
		},
	); err != nil {
		return err
	}

	ctx, s.cancelSync = context.WithCancel(ctx)
	s.syncStopWait.Add(1)

	go func() {
		err = conn.SyncWithContext(ctx)
		defer s.syncStopWait.Done()
		if err != nil && !errors.Is(err, context.Canceled) {
			conn.Log.Err(err).Msg("Sync error")
		}
	}()

	return nil
}

func (s *Service) Close() error {
	if s.matrixConn == nil {
		return nil
	}
	defer s.matrixConn.Close()

	if s.cancelSync != nil {
		s.Log.Trace().Msg("Stopping syncer")
		s.cancelSync()
		s.Log.Trace().Msg("Waiting for syncer to stop")
		s.syncStopWait.Wait()
		s.Log.Trace().Msg("Syncer stopped")
	}

	return nil
}

type ChatMessageConsumer struct {
}

func (c *ChatMessageConsumer) Consume(
	ctx context.Context,
	m *messaging.Message,
) error {
	msg, err := m.Text()
	if err == nil {
		log.Println("INFO:", msg)
	}
	return err
}
