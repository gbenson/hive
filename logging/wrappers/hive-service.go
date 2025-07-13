package wrappers

import (
	"iter"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/wrappers/internal"
)

// HiveServiceEvent represents a JSON-formatted event logged by a
// Hive service.
type HiveServiceEvent struct {
	WrappedEvent
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

// hiveServicePairs declares which fields to omit from Pairs.
var hiveServicePairs = OmitPairs(LoggerTagField, "level")

// init registers an event modifier that returns a new HiveServiceEvent
// if the given event represents a JSON-formatted log event logged by a
// Hive service.
func init() {
	registerWrapper("hive-service", func(e Event) Event {
		switch LoggerTag(e) {
		case "hive-service-go":
			return &HiveGoServiceEvent{HiveServiceEvent{Wrap(e)}}
		case "hive-service-py":
			return &HivePyServiceEvent{HiveServiceEvent{Wrap(e)}}
		default:
			return e // not a Hive service event
		}
	})
}

// Priority returns the syslog severity level of this event.
func (e *HiveGoServiceEvent) Priority() Priority {
	return ZerologPriorityMap.Get(Field(e, "level"))
}

// Priority returns the syslog severity level of this event.
func (e *HivePyServiceEvent) Priority() Priority {
	return PythonPriorityMap.Get(Field(e, "level"))
}

// Message implements the [Event] interface.
func (e *HiveServiceEvent) Message() Message {
	return e
}

// Pairs returns ordered key-value pairs for message construction.
func (e *HiveServiceEvent) Pairs() iter.Seq2[string, any] {
	return hiveServicePairs(e.Wrapped.Message().Pairs())
}
