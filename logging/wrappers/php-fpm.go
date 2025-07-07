package wrappers

import (
	"iter"
	"strconv"
	"time"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/wrappers/internal"

	"gbenson.net/hive/logging/internal/rxp"
	"gbenson.net/hive/logging/internal/rxparser"
)

// PHPFPMAccessEvent represents an access_log event logged by PHP-FPM.
type PHPFPMAccessEvent struct {
	WrappedEvent

	Timestamp  time.Time `json:"timestamp"`
	RemoteAddr string    `json:"remote_addr"`
	RemoteUser string    `json:"remote_user,omitempty"`
	Method     string    `json:"request_method"`
	RequestURI string    `json:"request_uri"`
	StatusCode int       `json:"status"`
}

// phpFPMAccessLogParser parses PHP-FPM access log messages.
var phpFPMAccessLogParser = rxparser.MustCompile(rxp.PHPFPMAccessLogEntry)

// commonLogTimeFormat is the time format used in common/combined
// format httpd access logs.
const commonLogTimeFormat = "02/Jan/2006:15:04:05 -0700"

// init registers an event modifier that returns a new PHPFPMAccessEvent
// if the given event represents an access_log event logged by PHP-FPM.
func init() {
	registerWrapper("php-fpm-access", func(e Event) Event {
		msg := e.Message()
		if len(msg.Fields()) > 0 {
			return e // already structured
		}

		fields := phpFPMAccessLogParser.ParseString(msg.String())
		if len(fields) < 7 {
			return e // no match
		}

		s := fields["timestamp"]
		timestamp, err := time.Parse(commonLogTimeFormat, s)
		if err != nil {
			Logger.Warn().
				Err(err).
				Str("input", s).
				Msg("Bad timestamp")
		}

		s = fields["status"]
		status, err := strconv.Atoi(s)
		if err != nil {
			Logger.Warn().
				Err(err).
				Str("input", s).
				Msg("Bad HTTP status code")
		}

		return &PHPFPMAccessEvent{
			WrappedEvent: Wrap(e),

			Timestamp:  timestamp,
			RemoteAddr: fields["remote_addr"],
			RemoteUser: fields["remote_user"],
			Method:     fields["method"],
			RequestURI: fields["request_uri"],
			StatusCode: status,
		}
	})
}

// Priority returns the syslog severity level of this event.
func (e *PHPFPMAccessEvent) Priority() Priority {
	return PriorityFromHTTPStatus(e.StatusCode)
}

// Message implements the [Event] interface.
func (e *PHPFPMAccessEvent) Message() Message {
	return e
}

// Pairs implements the [Message] interface. The field names match
// what Nginx records in its *error* log, for ease of correlation.
func (e *PHPFPMAccessEvent) Pairs() iter.Seq2[string, any] {
	return func(yield func(string, any) bool) {
		for _, pair := range []struct {
			k string
			v any
		}{
			{"client", e.RemoteAddr},
			{"user", e.RemoteUser},
			{"method", e.Method},
			{"uri", e.RequestURI},
			{"status", e.StatusCode},
		} {
			if s, ok := pair.v.(string); ok && s == "" {
				continue // no empty strings
			}
			if !yield(pair.k, pair.v) {
				return
			}
		}
	}
}
