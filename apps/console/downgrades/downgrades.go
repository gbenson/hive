package downgrades

import (
	"gbenson.net/hive/logging"
	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/wrappers"
)

// downgradedEvent represents a event that has had its priority
// downgraded for nicer printing.
type downgradedEvent struct {
	WrappedEvent
	priority Priority
}

// Priority returns the syslog severity level of this event.
func (e *downgradedEvent) Priority() Priority {
	return e.priority
}

// registerWrapper registers a wrapper with UnmarshalEvent.
func registerDowngrade(name string, newpri Priority, f func(e Event) bool) {
	logging.RegisterModifier("downgrade-"+name, func(e Event) Event {
		if !f(e) {
			return e
		}
		return &downgradedEvent{Wrap(e), newpri}
	})
}
