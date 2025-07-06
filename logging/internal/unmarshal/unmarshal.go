// Package unmarshal provides the UnmarshalEvent function.
package unmarshal

import (
	logging "gbenson.net/hive/logging/event"
	"gbenson.net/hive/logging/internal/modifiers"
	"gbenson.net/hive/logging/sources"
	"gbenson.net/hive/messaging"
)

// UnmarshalEvent unmarshals a [messaging.Event] into a [logging.Event].
func UnmarshalEvent(me *messaging.Event) (logging.Event, error) {
	e, err := sources.UnmarshalEvent(me)
	if err != nil {
		return nil, err
	}

	return modifiers.Apply(e), nil
}
