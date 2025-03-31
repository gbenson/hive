// Package chat sends chat events for Hive services.
package chat

import (
	"context"
	"fmt"
	"time"

	"gbenson.net/hive/messaging"
)

const (
	SendTextRequestsQueue     = "matrix.send.text.requests"
	SendReactionRequestsQueue = "matrix.send.reaction.requests"
	UserTypingRequestsQueue   = "matrix.user.typing.requests"
)

type SendTextRequest struct {
	Text string `json:"text"`
}

type SendReactionRequest struct {
	EventID  string `json:"event_id"`
	Reaction string `json:"reaction"`
}

type UserTypingRequest struct {
	Timeout time.Duration `json:"timeout"`
}

func (m *SendTextRequest) MarshalEvent() (*messaging.Event, error) {
	e := messaging.NewEvent()
	e.SetData("application/json", m)
	return e, nil
}

func (m *SendTextRequest) UnmarshalEvent(e *messaging.Event) error {
	if e.Type() != "net.gbenson.hive.matrix_send_text_request" {
		return fmt.Errorf("unexpected event type %q", e.Type())
	}
	return e.DataAs(m)
}

func (m *SendReactionRequest) UnmarshalEvent(e *messaging.Event) error {
	if e.Type() != "net.gbenson.hive.matrix_send_reaction_request" {
		return fmt.Errorf("unexpected event type %q", e.Type())
	}
	return e.DataAs(m)
}

func (m *UserTypingRequest) UnmarshalEvent(e *messaging.Event) error {
	if e.Type() != "net.gbenson.hive.matrix_user_typing_request" {
		return fmt.Errorf("unexpected event type %q", e.Type())
	}
	return e.DataAs(m)
}

func TellUser(ctx context.Context, ch messaging.Channel, s string) error {
	r := SendTextRequest{s}
	return ch.PublishEvent(ctx, SendTextRequestsQueue, &r)
}
