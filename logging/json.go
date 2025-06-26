package logging

import (
	"encoding/json"
	"iter"
	"maps"
	"slices"
)

// jsonEvent represents a logged event whose message is a JSON-encoded
// dictionary.
type jsonEvent struct {
	wrappedEvent
	fields map[string]any
}

func maybeWrapJSONEvent(e Event) Event {
	msg := e.Message()
	if len(msg.Fields()) > 0 {
		return e // already structured
	}

	// Quickly bail if the message can't be a JSON dict.
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

	return &jsonEvent{wrappedEvent{e}, m}
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
	return func(yield func(string, any) bool) {
		msg := e.fields

		// Output any "message" component first, if present.
		var hoisted string
		for _, k := range []string{"message", "msg"} {
			v := StringField(e, k)
			if v == "" {
				continue
			}
			if !yield(k, v) {
				return
			}
			hoisted = k
			break
		}

		keys := slices.Sorted(maps.Keys(msg))
		for _, k := range keys {
			if k == hoisted {
				continue
			}
			if !yield(k, msg[k]) {
				return
			}
		}
	}
}
