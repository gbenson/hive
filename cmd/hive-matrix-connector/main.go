// hive-matrix-connector is the Matrix connector service for Hive.
package main

import (
	"context"
	"errors"
	"sync"
	"time"

	"gbenson.net/hive/matrix"
	"gbenson.net/hive/messaging"
	"gbenson.net/hive/service"
)

func main() {
	service.Run(&Service{})
}

type Service struct {
	matrixConn   *matrix.Conn
	cancelSync   context.CancelFunc
	syncStopWait sync.WaitGroup
}

func (s *Service) Start(ctx context.Context, ch *messaging.Channel) error {
	if err := s.startMatrix(ctx, ch); err != nil {
		return err
	}

	return nil
}

func (s *Service) startMatrix(ctx context.Context, ch *messaging.Channel) error {
	conn, err := matrix.DialContext(ctx, &matrix.DialOptions{ConfigKey: "hive"})
	if err != nil {
		return err
	}
	s.matrixConn = conn

	if err := conn.OnEventType(
		matrix.EventMessage,
		func(ctx context.Context, e *matrix.Event) {
			if err := s.onEventMessage(ctx, e, ch); err != nil {
				conn.Log.Err(err).Msg("")
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
	conn := s.matrixConn
	if conn == nil {
		return nil
	}
	defer conn.Close()

	if s.cancelSync != nil {
		conn.Log.Trace().Msg("Stopping syncer")
		s.cancelSync()
		conn.Log.Trace().Msg("Waiting for syncer to stop")
		s.syncStopWait.Wait()
		conn.Log.Trace().Msg("Syncer stopped")
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

	event := messaging.NewEvent()
	event.SetID(e.ID.String())
	event.SetType("net.gbenson.hive.matrix_event")
	event.SetTime(time.UnixMilli(e.Timestamp))
	event.SetSubject(e.Type.String())
	event.SetData(messaging.ApplicationJSON, data)

	return ch.PublishEvent(ctx, "matrix.events", event)
}
