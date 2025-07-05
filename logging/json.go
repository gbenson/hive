package logging

import (
	"encoding/json"
	"iter"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/internal"
)

// jsonEvent represents a logged event whose message is a JSON-encoded
// dictionary.
type jsonEvent struct {
	wrappedEvent
	fields map[string]any
}

// init registers a handler that returns a new jsonEvent if the given
// event represents a logged event whose message is a JSON-encoded
// dictionary.
func init() {
	RegisterHandler("json", func(e Event) Event {
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

		return &jsonEvent{Wrap(e), m}
	})
}

// Message implements the [Event] interface.
func (e *jsonEvent) Message() Message {
	return e
}

// Fields implements the [Message] interface.
func (e *jsonEvent) Fields() map[string]any {
	return e.fields
}

// Pairs implements the [Message] interface.
func (e *jsonEvent) Pairs() iter.Seq2[string, any] {
	return SortedPairs(e)
}
