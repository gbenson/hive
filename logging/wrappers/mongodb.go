package wrappers

import (
	"iter"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/wrappers/internal"
)

// MongoDBEvent represents a JSON-formatted event logged by MongoDB.
type MongoDBEvent struct {
	WrappedEvent
}

// mongoDBExpectFields is the fields we require to be present to
// consider a JSON-formatted log event to be from MongoDB, except.
// "t" which is checked separately.
var mongoDBExpectFields = []string{"s", "c", "id", "ctx", "msg"}

// mongoDBPairs declares which fields to omit from Pairs.
var mongoDBPairs = OmitPairs("t", "s") // timestamp, severity

// mongoDBPriorityMap maps MongoDB severity levels to syslog severity
// levels.
// https://www.mongodb.com/docs/manual/reference/log-messages/#severity
var mongoDBPriorityMap = PriorityMap{
	"D5": PriDebug,
	"D4": PriDebug,
	"D3": PriDebug,
	"D2": PriDebug,
	"D1": PriDebug,
	"I":  PriInfo,
	"W":  PriWarning,
	"E":  PriErr,
	"F":  PriCrit,
}

// init registers an event modifier that returns a new MongoDBEvent
// if the given event represents a JSON-formatted log event logged
// by MongoDB.
func init() {
	registerWrapper("mongodb", func(e Event) Event {
		fields := e.Message().Fields()

		// "Each log entry is output as a self-contained JSON object
		// which follows the Relaxed Extended JSON v2.0 specification,
		// and has the following layout and field order:
		//
		// {
		//   "t": <Datetime>, // timestamp
		//   "s": <String>, // severity
		//   "c": <String>, // component
		//   "id": <Integer>, // unique identifier
		//   "ctx": <String>, // context
		//   "svc": <String>, // service
		//   "msg": <String>, // message body
		//   ...
		//
		// https://www.mongodb.com/docs/manual/reference/log-messages/
		// #json-log-output-format
		if len(fields) < 6 {
			return e // not a MongoDB log entry
		}
		if t, ok := fields["t"]; !ok {
			return e // not a MongoDB log entry
		} else if tt, ok := t.(map[string]any); !ok {
			return e // not a MongoDB log entry
		} else if _, ok := tt["$date"]; !ok {
			return e // not a MongoDB log entry
		}

		for _, field := range mongoDBExpectFields {
			if _, ok := fields[field]; !ok {
				return e // not a MongoDB log entry
			}
		}

		// Final check, since we don't set LoggerTagField on these...
		if _, ok := fields[LoggerTagField]; ok {
			return e // not a MongoDB log entry
		}

		// Could bson.UnmarshalExtJSON at this point, like
		// we do for NginxAccessEvent, if that's useful.

		return &MongoDBEvent{Wrap(e)}
	})
}

// Priority returns the syslog severity level of this event.
func (e *MongoDBEvent) Priority() Priority {
	return mongoDBPriorityMap.Get(Field(e, "s"))
}

// Message implements the [Event] interface.
func (e *MongoDBEvent) Message() Message {
	return e
}

// Pairs returns ordered key-value pairs for message construction.
func (e *MongoDBEvent) Pairs() iter.Seq2[string, any] {
	return mongoDBPairs(e.Wrapped.Message().Pairs())
}
