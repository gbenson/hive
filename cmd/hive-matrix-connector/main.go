// hive-matrix-connector is the Matrix connector service for Hive.
package main

import (
	"context"
	"errors"
	"log"
	"sync"
	"time"

	cloudevents "github.com/cloudevents/sdk-go/v2"
	"github.com/rs/zerolog"

	"gbenson.net/hive/matrix"
	"gbenson.net/hive/messaging"
	"gbenson.net/hive/service"
	"gbenson.net/hive/util"
)

func main() {
	service.Run(&Service{})
}

type Service struct {
	Name string
	Log  zerolog.Logger

	matrixConn   *matrix.Conn
	cancelSync   context.CancelFunc
	syncStopWait sync.WaitGroup

	cmc ChatMessageConsumer
}

func (s *Service) Start(ctx context.Context, ch *messaging.Channel) error {
	s.Name = util.ServiceNameURL()
	s.Log = zerolog.New(zerolog.NewConsoleWriter())

	if err := s.startMatrix(ctx, ch); err != nil {
		return err
	}

	if err := ch.ConsumeEvents(ctx, "chat.messages", &s.cmc); err != nil {
		return err
	}

	return nil
}

func (s *Service) startMatrix(ctx context.Context, ch *messaging.Channel) error {
	conn, err := matrix.Dial(&matrix.DialOptions{ConfigKey: "hive", Log: s.Log})
	if err != nil {
		return err
	}
	s.matrixConn = conn

	if err := conn.OnEventType(
		matrix.EventMessage,
		func(ctx context.Context, e *matrix.Event) {
			if err := s.onEventMessage(ctx, e, ch); err != nil {
				s.Log.Err(err).Msg("")
			}
		},
	); err != nil {
		return err
	}

	ctx, s.cancelSync = context.WithCancel(ctx)
	s.syncStopWait.Add(1)

	go func() {
		err := conn.SyncWithContext(ctx)
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

func (s *Service) onEventMessage(
	ctx context.Context,
	e *matrix.Event,
	ch *messaging.Channel,
) error {
	data, err := matrix.MarshalEvent(e)
	if err != nil {
		return err
	}

	event := cloudevents.NewEvent()
	event.SetID(e.ID.String())
	event.SetSource(s.Name)
	event.SetType("net.gbenson.hive.matrix_event")
	event.SetTime(time.UnixMilli(e.Timestamp))
	event.SetSubject(e.Type.String())
	event.SetData(cloudevents.ApplicationJSON, data)

	return ch.PublishEvent(ctx, "matrix.events", event)
}

type ChatMessageConsumer struct {
}

func (c *ChatMessageConsumer) Consume(
	ctx context.Context,
	m *messaging.Message,
) error {
	msg, err := m.Text()
	if err == nil {
		log.Printf("\x1B[34mINFO: hive.chat.message: %v\x1B[0m", msg)
	}
	return err
}
