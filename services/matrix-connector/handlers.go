package matrix

import (
	"context"

	"gbenson.net/hive/chat"
	"gbenson.net/hive/logger"
	"gbenson.net/hive/messaging"

	"maunium.net/go/mautrix/id"
)

type requestHandler interface {
	messaging.Consumer
	Queue() string
}

// sendTextRequestHandler handles SendText requests.
type sendTextRequestHandler struct {
	Service *Service
}

func (h *sendTextRequestHandler) Queue() string {
	return chat.SendTextRequestsQueue
}

func (h *sendTextRequestHandler) Consume(
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

	s := h.Service
	resp, err := s.Client.SendText(ctx, s.RoomID, r.Text)
	if err != nil {
		return err
	}

	logger.Ctx(ctx).Info().
		Str("event_id", resp.EventID.String()).
		Str("text", r.Text).
		Msg("Message sent")

	return nil
}

// sendReactionRequestHandler handles SendReaction requests.
type sendReactionRequestHandler struct {
	Service *Service
}

func (h *sendReactionRequestHandler) Queue() string {
	return chat.SendReactionRequestsQueue
}

func (h *sendReactionRequestHandler) Consume(
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

	s := h.Service
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
		Msg("Reaction sent")

	return nil
}

// userTypingRequestHandler handles UserTyping requests.
type userTypingRequestHandler struct {
	Service *Service
}

func (h *userTypingRequestHandler) Queue() string {
	return chat.UserTypingRequestsQueue
}

func (h *userTypingRequestHandler) Consume(
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

	s := h.Service
	typing := r.Timeout > 0
	_, err := s.Client.UserTyping(ctx, s.RoomID, typing, r.Timeout)
	if err != nil {
		return err
	}

	logger.Ctx(ctx).Info().
		Bool("user_typing", typing).
		Dur("timeout", r.Timeout).
		Msg("Typing status set")

	return nil
}
