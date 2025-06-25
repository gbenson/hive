// Package logging provides centralized logging services for Hive.
package logging

import (
	"fmt"

	"gbenson.net/hive/logging/event"
	"gbenson.net/hive/logging/systemd"
	"gbenson.net/hive/messaging"
)

// EventsQueue is where log collectors publish the events they collect.
const EventsQueue = systemd.EventsQueue

// Event represents a single logged event.
type Event = event.Event

// UnmarshalEvent unmarshals a [messaging.Event] into an [Event].
func UnmarshalEvent(e *messaging.Event) (Event, error) {
	switch e.Type() {
	case systemd.EventType:
		return systemd.UnmarshalEvent(e)

	default:
		return nil, fmt.Errorf("unexpected event type %q", e.Type())
	}
}
