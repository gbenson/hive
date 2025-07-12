package analyser

import (
	"maps"
	"strings"
	"time"

	"gbenson.net/hive/logging"
	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/wrappers"
)

// preLoggerTagEvent represents a JSON-formatted event emitted before
// such events were emitted with a "net_gbenson_logger" logger tag
// field for identification, that would have such a logger tag field
// if emitted today.
type preLoggerTagEvent struct {
	WrappedEvent
	fields map[string]any
}

// preLoggerTagCutoff is the time after which all hive-service and
// nginx JSON-formatted messages have a "net_gbenson_logger" field
// for identification.
var preLoggerTagCutoff = time.Date(2025, 6, 26, 19, 24, 0, 0, time.UTC)

// init registers an event modifier that returns a new preLoggerTagEvent
// if the given event represents a JSON-formatted event emitted before
// preLoggerTagCutoff that would have a logger tag if emitted today.
func init() {
	logging.RegisterModifier("pre-logger-tag", func(e Event) Event {
		if _, ok := e.(*JSONEvent); !ok {
			return e // not a JSON-formatted event
		} else if LoggerTag(e) != "" {
			return e // event has a logger tag field
		} else if e.Time().After(preLoggerTagCutoff) {
			return e // event isn't old enough.
		}

		loggerTag := loggerTagFor(e)
		if loggerTag == "" {
			return e // don't synthesize a logger tag.
		}

		r := &preLoggerTagEvent{WrappedEvent: Wrap(e)}
		r.fields = maps.Clone(e.Message().Fields()) // shallow copy
		r.fields[LoggerTagField] = loggerTag

		return r
	})
}

// loggerTagFor returns a synthetic logger tag for the given event.
func loggerTagFor(e Event) string {
	s, found := strings.CutPrefix(e.ContainerName(), "hive-")
	if !found {
		return "" // container name doesn't start with "hive-"
	}

	if strings.HasPrefix(s, "nginx-") {
		if e.Priority() != PriInfo {
			return "" // not an access-log event
		}

		return "nginx" // NginxAccessLogEvent
	}

	return "hive-service-go"
}

// Message implements the [Event] interface.
func (e *preLoggerTagEvent) Message() Message {
	return e
}

// Fields implements the [Message] interface.
func (e *preLoggerTagEvent) Fields() map[string]any {
	return e.fields
}
