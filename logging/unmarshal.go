// Package logging provides centralized logging services for Hive.
package logging

import (
	"fmt"
	"maps"

	. "gbenson.net/hive/logging/event"
	"gbenson.net/hive/logging/systemd"
	"gbenson.net/hive/messaging"
)

// A EventHandlerFunc either transforms an event or returns it
// unmodified.
type EventHandlerFunc func(Event) Event

// eventHandlers are the registered event handlers.
var eventHandlers = map[string]EventHandlerFunc{}

// RegisterHandler registers a new event handler.
func RegisterHandler(name string, f EventHandlerFunc) {
	eventHandlers[name] = f
}

// UnmarshalEvent unmarshals a [messaging.Event] into an [Event].
func UnmarshalEvent(me *messaging.Event) (Event, error) {
	e, err := unmarshalEvent(me)
	if err != nil {
		return nil, err
	}

	// Loop over handlers until all return unmodified.
	handlers := maps.Clone(eventHandlers)
loop:
	for len(handlers) != 0 {
		for name, maybeWrap := range handlers {
			if ee := maybeWrap(e); ee != e {
				e = ee
				Logger.Trace().
					Str("event", e.ID()).
					Str("handler", name).
					Msg("Wrapped")

				delete(handlers, name)
				continue loop
			}
		}
		break // no handlers fired
	}

	return e, nil
}

func unmarshalEvent(e *messaging.Event) (Event, error) {
	switch e.Type() {
	case systemd.EventType:
		return systemd.UnmarshalEvent(e)

	default:
		return nil, fmt.Errorf("unexpected event type %q", e.Type())
	}
}
