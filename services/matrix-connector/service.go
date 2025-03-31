package matrix

import (
	"context"
	"encoding/json"
	"errors"
	"sync"
	"time"

	"gbenson.net/hive/logger"
	"gbenson.net/hive/messaging"

	"maunium.net/go/mautrix/event"
	"maunium.net/go/mautrix/id"
)

type Service struct {
	Options      Options
	Client       *Client
	RoomID       id.RoomID
	cancelSync   context.CancelFunc
	syncStopWait sync.WaitGroup
	consumers    []requestHandler
}

func (s *Service) Start(ctx context.Context, ch messaging.Channel) (err error) {
	if s.Options.Log == nil {
		s.Options.Log = logger.Ctx(ctx)
	}
	if err = s.Options.Populate(); err != nil {
		return
	}
	s.RoomID = id.RoomID(s.Options.RoomID)

	if s.Client, err = Dial(ctx, &s.Options); err != nil {
		return
	}

	for _, eventType := range []event.Type{
		event.EventMessage,
		event.EventReaction,
	} {
		if err = s.Client.OnEventType(
			eventType,
			func(ctx context.Context, e *event.Event) {
				if err := s.onEventMessage(ctx, e, ch); err != nil {
					s.Client.Log.Err(err).Msg("")
				}
			},
		); err != nil {
			return
		}
	}

	ctx, s.cancelSync = context.WithCancel(ctx)
	s.syncStopWait.Add(1)

	go func() {
		err := s.Client.SyncWithContext(ctx)
		defer s.syncStopWait.Done()
		if err != nil && !errors.Is(err, context.Canceled) {
			s.Client.Log.Err(err).Msg("Sync error")
		}
	}()

	s.consumers = []requestHandler{
		&sendTextRequestHandler{s},
		&sendReactionRequestHandler{s},
		&userTypingRequestHandler{s},
	}
	for _, c := range s.consumers {
		if err := ch.ConsumeEvents(ctx, c.Queue(), c); err != nil {
			return err
		}
	}
	return nil
}

func (s *Service) Close() error {
	conn := s.Client
	if conn == nil {
		return nil
	}
	defer logger.LoggedClose(&conn.Log, conn, "Matrix client")

	if s.cancelSync != nil {
		conn.Log.Debug().Msg("Stopping syncer")
		s.cancelSync()
		conn.Log.Debug().Msg("Waiting for syncer to stop")
		s.syncStopWait.Wait()
		conn.Log.Debug().Msg("Syncer stopped")
	}

	return nil
}

// onEventMessage translates a received [matrix.EventMessage] into a
// [messaging.Event] and publishes it to the "matrix.events" exchange.
func (s *Service) onEventMessage(
	ctx context.Context,
	e *event.Event,
	ch messaging.Channel,
) error {
	b, err := e.MarshalJSON()
	if err != nil {
		return err
	}

	var v interface{}
	if err := json.Unmarshal(b, &v); err != nil {
		return err
	}

	event := messaging.NewEvent()
	event.SetID(e.ID.String())
	event.SetTime(time.UnixMilli(e.Timestamp))
	event.SetSubject(e.Type.String())
	event.SetData("application/json", v)

	return ch.PublishEvent(ctx, "matrix.events", event)
}
