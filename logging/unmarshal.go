// Package logging provides centralized logging services for Hive.
package logging

import (
	"fmt"

	. "gbenson.net/hive/logging/event"
	"gbenson.net/hive/logging/systemd"
	"gbenson.net/hive/messaging"
)

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
