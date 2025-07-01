package logging

import (
	"iter"

	. "gbenson.net/hive/logging/event"
)

// HiveServiceEvent represents a JSON-formatted event logged by a
// Hive service.
type HiveServiceEvent struct {
	wrappedEvent
}

// HiveGoServiceEvent represents a JSON-formatted event logged by
// a Hive service written in Go.
type HiveGoServiceEvent struct {
	HiveServiceEvent
}

// HivePyServiceEvent represents a JSON-formatted event logged by
// a Hive service written in Python.
type HivePyServiceEvent struct {
	HiveServiceEvent
}

// hiveServiceMQPairs declares which fields to omit from Pairs.
var hiveServicePairs = omitPairs(LoggerTagField, "level")

// maybeWrapHiveServiceEvent returns a new HiveServiceEvent if the
// given event represents a JSON-formatted event logged by a Hive
// service. In all other cases the given event is returned unmodified.
func maybeWrapHiveServiceEvent(e Event) Event {
	switch LoggerTag(e) {
	case "hive-service-go":
		return &HiveGoServiceEvent{HiveServiceEvent{wrappedEvent{e}}}
	case "hive-service-py":
		return &HivePyServiceEvent{HiveServiceEvent{wrappedEvent{e}}}
	default:
		return e // not a Hive service event
	}
}

// Priority returns the syslog severity level of this event.
func (e *HiveGoServiceEvent) Priority() Priority {
	return zerologPriorityMap.Get(Field(e, "level"))
}

// Priority returns the syslog severity level of this event.
func (e *HivePyServiceEvent) Priority() Priority {
	return pythonPriorityMap.Get(Field(e, "level"))
}

// Message implements the [Event] interface.
func (e *HiveServiceEvent) Message() Message {
	return e
}

// Pairs returns ordered key-value pairs for message construction.
func (e *HiveServiceEvent) Pairs() iter.Seq2[string, any] {
	return hiveServicePairs(e.w.Message().Pairs())
}
