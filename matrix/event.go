package matrix

import (
	"encoding/json"
	"maunium.net/go/mautrix/event"
)

type Event = event.Event

var (
	EventMessage   = event.EventMessage
	EventReaction  = event.EventReaction
	EventRedaction = event.EventRedaction
)

// MarshalEvent marshals an Event into an interface with the field names
// defined in the [Client-Server API] section of the Matrix Specification.
//
// [Client-Server API]: https://spec.matrix.org/latest/client-server-api/#events
func MarshalEvent(e *Event) (any, error) {
	b, err := e.MarshalJSON()
	if err != nil {
		return nil, err
	}

	var v interface{}
	if err = json.Unmarshal(b, &v); err != nil {
		return nil, err
	}

	return v, nil
}
