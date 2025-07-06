// Package sources provides logger-specific Event implementations.
package sources

import (
	"fmt"

	logging "gbenson.net/hive/logging/event"
	"gbenson.net/hive/logging/sources/systemd"
	"gbenson.net/hive/messaging"
)

// UnmarshalEvent unmarshals a [messaging.Event] into a [logging.Event].
func UnmarshalEvent(e *messaging.Event) (logging.Event, error) {
	switch e.Type() {
	case systemd.EventType:
		return systemd.UnmarshalEvent(e)

	default:
		return nil, fmt.Errorf("unexpected event type %q", e.Type())
	}
}
