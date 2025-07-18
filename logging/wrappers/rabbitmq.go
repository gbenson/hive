package wrappers

import (
	"iter"
	"regexp"
	"time"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/wrappers/internal"
)

// RabbitMQEvent represents a JSON-formatted event logged by RabbitMQ.
type RabbitMQEvent struct {
	WrappedEvent
}

// rabbitMQPIDrx matches the "pid" field of RabbitMQ structured events.
var rabbitMQPIDrx = regexp.MustCompile(`^<\d+\.\d+\.\d+>$`)

// rabbitMQPairs declares which fields to omit from Pairs.
var rabbitMQPairs = OmitPairs("level", "time")

// rabbitMQPriorityMap maps RabbitMQ log levels to syslog severity
// levels.  https://www.rabbitmq.com/docs/logging#log-levels
var rabbitMQPriorityMap = PriorityMap{
	"debug":    PriDebug,
	"info":     PriInfo,
	"warning":  PriWarning,
	"error":    PriErr,
	"critical": PriCrit,
}

// rabbitMQTimeFormat is exactly what you think it is.
const rabbitMQTimeFormat = "2006-01-02 15:04:05.999999Z07:00"

// init registers an event modifier that returns a new RabbitMQEvent if
// the given event represents a JSON-formatted event logged by RabbitMQ.
func init() {
	registerWrapper("rabbitmq", func(e Event) Event {
		pid := StringField(e, "pid")
		if len(pid) < 7 || !rabbitMQPIDrx.MatchString(pid) {
			return e
		}

		return &RabbitMQEvent{Wrap(e)}
	})
}

// Priority returns the syslog severity level of this event.
func (e *RabbitMQEvent) Priority() Priority {
	return rabbitMQPriorityMap.Get(Field(e, "level"))
}

// Time returns the wallclock timestamp of this event.
func (e *RabbitMQEvent) Time() time.Time {
	jtime := e.Wrapped.Time()

	s := StringField(e, "time")
	rtime, err := time.Parse(rabbitMQTimeFormat, s)
	if err != nil {
		Logger.Warn().
			Err(err).
			Str("format", rabbitMQTimeFormat).
			Str("input", s).
			Msg("time.Parse failed")
		return jtime
	}

	// The time RabbitMQ reported should be slightly older than
	// the time journald recorded, e.g. ~1.4ms on unloaded rpi4.
	d := jtime.Sub(rtime)
	if d < 0 || d > time.Hour {
		Logger.Warn().
			Dur("delta", d).
			Time("journald_time", jtime).
			Time("rabbitmq_time", rtime).
			Msg("Unexpected skew")
		return jtime
	}

	return rtime
}

// Message implements the [Event] interface.
func (e *RabbitMQEvent) Message() Message {
	return e
}

// Pairs returns ordered key-value pairs for message construction.
func (e *RabbitMQEvent) Pairs() iter.Seq2[string, any] {
	return rabbitMQPairs(e.Wrapped.Message().Pairs())
}
