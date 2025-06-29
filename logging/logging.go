// Package logging provides centralized logging services for Hive.
package logging

import (
	"fmt"

	"gbenson.net/go/logger"
	"gbenson.net/hive/logging/event"
	"gbenson.net/hive/logging/systemd"
	"gbenson.net/hive/messaging"
)

// EventsQueue is where log collectors publish the events they collect.
const EventsQueue = systemd.EventsQueue

// Event represents a single logged event.
type Event = event.Event

// Message represents the primary content of a logged event.
type Message = event.Message

// Priority is the RFC 5424 syslog severity level of an event.
type Priority = event.Priority

const (
	PriEmerg   = event.PriEmerg
	PriAlert   = event.PriAlert
	PriCrit    = event.PriCrit
	PriErr     = event.PriErr
	PriWarning = event.PriWarning
	PriNotice  = event.PriNotice
	PriInfo    = event.PriInfo
	PriDebug   = event.PriDebug
	PriUnknown = event.PriUnknown
)

// Logger is used to report errors that would otherwise be ignored.
// Be sure to avoid loops if you enable this.
var defaultLogger = logger.New(&logger.Options{Level: "disabled"})
var Logger = &defaultLogger

// UnmarshalEvent unmarshals a [messaging.Event] into an [Event].
func UnmarshalEvent(me *messaging.Event) (Event, error) {
	e, err := unmarshalEvent(me)
	if err != nil {
		return nil, err
	}

	// format-specific wrappers
	e = maybeWrapJSONEvent(e)

	// application-specific wrappers
	e = maybeWrapRabbitMQEvent(e)

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
