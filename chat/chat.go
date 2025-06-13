// Package chat defines Matrix chat events for Hive services.
package chat

// Note: Everything regarding chat on the Python side is now almost
// entirely handled by methods on messaging.Channel.  All that's in
// Python hive-chat now, IIRC, other than transition-supporting code
// that's almost certainly no-longer used is some shims for calling
// chat functions without an open channel, in v2.py and util.py, and
// even those might not be used.  TL;dr don't build up this package
// without seeing if somewhere else is a better fit for what you're
// adding.

import (
	"fmt"
	"time"

	"gbenson.net/hive/messaging"
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

/*
func (m *SendTextRequest) MarshalEvent() (*messaging.Event, error) {
	e := messaging.NewEvent()
	e.SetData("application/json", m)
	return e, nil
}
*/

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

/*
func TellUser(ctx context.Context, ch messaging.Channel, s string) error {
	r := SendTextRequest{s}
	return ch.PublishEvent(ctx, SendTextRequestsQueue, &r)
}
*/
