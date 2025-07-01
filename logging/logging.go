// Package logging provides centralized logging services for Hive.
package logging

import (
	"fmt"

	"gbenson.net/go/logger"
	"gbenson.net/hive/logging/event"
	"gbenson.net/hive/logging/systemd"
	"gbenson.net/hive/messaging"
)

// Event represents a single logged event.
type Event = event.Event

// Message represents the primary content of a logged event.
type Message = event.Message

// LoggerTagField is a field that can be added to structured log
// entries to avoid having to guess how they should be parsed.
const LoggerTagField = "net_gbenson_logger"

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
	e = maybeWrapHiveServiceEvent(e)
	e = maybeWrapNginxAccessEvent(e)
	e = maybeWrapNginxErrorEvent(e)
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
