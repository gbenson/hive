// Package chat defines Matrix chat events for Hive services.
package chat

// Note: Everything regarding chat on the Python side is now handled
// by methods on messaging.Channel; there is no Python hive-chat any
// more, so don't build up this package without considering whether
// somewhere else is a better fit for what you're adding.

import (
	"fmt"
	"time"

	"gbenson.net/hive/messaging"
)

type SendTextRequest struct {
	Text string `json:"text,omitempty"`
	HTML string `json:"html,omitempty"`
}

type SendReactionRequest struct {
	EventID  string `json:"event_id"`
	Reaction string `json:"reaction"`
}

type UserTypingRequest struct {
	Timeout time.Duration `json:"timeout"`
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
