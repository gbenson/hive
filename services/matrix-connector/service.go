package matrix

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"sync"
	"time"

	"gbenson.net/go/logger"
	"gbenson.net/hive/chat"
	"gbenson.net/hive/messaging"
	"gbenson.net/hive/messaging/matrix"

	"maunium.net/go/mautrix/event"
	"maunium.net/go/mautrix/id"
)

type Service struct {
	Options      Options
	Client       *Client
	RoomID       id.RoomID
	cancelSync   context.CancelFunc
	syncStopWait sync.WaitGroup
}

func (s *Service) Start(ctx context.Context, ch messaging.Channel) (err error) {
	log := logger.Ctx(ctx)

	if s.Options.Log == nil {
		s.Options.Log = log
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
				ctx = log.WithContext(ctx) // Remove go-mautrix additions
				if err := s.onEventMessage(ctx, e, ch); err != nil {
					log.Err(err).Msg("")
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
			log.Err(err).Msg("Sync error")
		}
	}()

	return ch.ConsumeEvents(ctx, matrix.RequestsQueue, s)
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

	logger.Ctx(ctx).Info().
		Interface("event", v).
		Msg("Received")

	event := messaging.NewEvent()
	event.SetID(e.ID.String())
	event.SetTime(time.UnixMilli(e.Timestamp))
	event.SetSubject(e.Type.String())
	event.SetData("application/json", v)

	return ch.PublishEvent(ctx, "matrix.events", event)
}

// Consume receives ...XXX
func (s *Service) Consume(
	ctx context.Context,
	ch messaging.Channel,
	e *messaging.Event,
) error {
	switch e.Type() {
	case "net.gbenson.hive.matrix_send_text_request":
		return s.consumeSendTextRequest(ctx, ch, e)

	case "net.gbenson.hive.matrix_send_reaction_request":
		return s.consumeSendReactionRequest(ctx, ch, e)

	case "net.gbenson.hive.matrix_user_typing_request":
		return s.consumeUserTypingRequest(ctx, ch, e)

	default:
		return fmt.Errorf("unexpected event type %q", e.Type())
	}
}

func (s *Service) consumeSendTextRequest(
	ctx context.Context,
	ch messaging.Channel,
	e *messaging.Event,
) error {
	var r chat.SendTextRequest
	if err := r.UnmarshalEvent(e); err != nil {
		return err
	}

	if r.Text == "" {
		return ErrBadRequest
	}

	resp, err := s.Client.SendText(ctx, s.RoomID, r.Text)
	if err != nil {
		return err
	}

	logger.Ctx(ctx).Info().
		Str("event_id", resp.EventID.String()).
		Str("text", r.Text).
		Msg("Sent")

	return nil
}

func (s *Service) consumeSendReactionRequest(
	ctx context.Context,
	ch messaging.Channel,
	e *messaging.Event,
) error {
	var r chat.SendReactionRequest
	if err := r.UnmarshalEvent(e); err != nil {
		return err
	}

	if r.EventID == "" {
		return ErrNoEventID
	}
	if r.Reaction == "" {
		return ErrBadRequest
	}

	resp, err := s.Client.SendReaction(
		ctx,
		s.RoomID,
		id.EventID(r.EventID),
		r.Reaction,
	)
	if err != nil {
		return err
	}

	logger.Ctx(ctx).Info().
		Str("event_id", resp.EventID.String()).
		Str("reaction", r.Reaction).
		Str("target_event_id", r.EventID).
		Msg("Sent")

	return nil
}

func (s *Service) consumeUserTypingRequest(
	ctx context.Context,
	ch messaging.Channel,
	e *messaging.Event,
) error {
	var r chat.UserTypingRequest
	if err := r.UnmarshalEvent(e); err != nil {
		return err
	}

	if r.Timeout < 0 {
		return ErrBadRequest
	}

	typing := r.Timeout > 0
	_, err := s.Client.UserTyping(ctx, s.RoomID, typing, r.Timeout)
	if err != nil {
		return err
	}

	logger.Ctx(ctx).Info().
		Bool("user_typing", typing).
		Dur("timeout", r.Timeout).
		Msg("Set")

	return nil
}
