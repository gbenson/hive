package wrappers

import (
	"encoding/json"
	"iter"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/wrappers/internal"
)

// JSONEvent represents a logged event whose message is a JSON-encoded
// dictionary.
type JSONEvent struct {
	WrappedEvent
	fields map[string]any
}

// init registers an event modifier that returns a new JSONEvent if
// the given event represents a logged event whose message is a
// JSON-encoded dictionary.
func init() {
	registerWrapper("json", func(e Event) Event {
		msg := e.Message()
		if len(msg.Fields()) > 0 {
			return e // already structured
		}

		// Quickly bail if the message can't be a JSON dictionary.
		s := msg.String()
		if len(s) < 3 || s[0] != '{' || s[len(s)-1] != '}' {
			return e
		}

		var m map[string]any
		if err := json.Unmarshal([]byte(s), &m); err != nil {
			return e
		}
		if len(m) == 0 {
			return e
		}

		return &JSONEvent{Wrap(e), m}
	})
}

// Message implements the [Event] interface.
func (e *JSONEvent) Message() Message {
	return e
}

// Fields implements the [Message] interface.
func (e *JSONEvent) Fields() map[string]any {
	return e.fields
}

// Pairs implements the [Message] interface.
func (e *JSONEvent) Pairs() iter.Seq2[string, any] {
	return SortedPairs(e)
}
