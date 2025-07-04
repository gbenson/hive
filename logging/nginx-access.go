package logging

import (
	"encoding/json"
	"iter"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/internal"
)

// NginxAccessEvent represents a JSON-formatted access_log event
// logged by Nginx.  This isn't a standard Nginx thing, just how
// Hive's Nginx containers are configured.
type NginxAccessEvent struct {
	wrappedEvent

	RemoteAddr   string  `json:"remote_addr"`
	RemoteUser   string  `json:"remote_user,omitempty"`
	Host         string  `json:"http_host,omitempty"`
	Method       string  `json:"request_method"`
	RequestURI   string  `json:"request_uri"`
	Proto        string  `json:"server_protocol"`
	TLSProto     string  `json:"ssl_protocol,omitempty"`
	StatusCode   int     `json:"status"`
	ResponseSize int     `json:"body_bytes_sent"`
	UserAgent    string  `json:"http_user_agent,omitempty"`
	Referer      string  `json:"http_referer,omitempty"`
	RequestSize  int     `json:"request_length"`
	Timestamp    float64 `json:"timestamp"`
}

// maybeWrapNginxAccessEvent returns a new NginxAccessEvent if the
// given event represents a JSON-formatted access_log event logged
// by Nginx.  Otherwise, the given event is returned unmodified.
func maybeWrapNginxAccessEvent(e Event) Event {
	if LoggerTag(e) != "nginx" {
		return e // not a Hive-style Nginx event
	}

	b, err := json.Marshal(e.Message().Fields())
	if err != nil {
		// shouldn't be possible without something modifying
		// what Fields() returns inbetween jsonEvent and us.
		Logger.Warn().
			Err(err).
			Str("original_input", e.Message().String()).
			Msg("json.Marshal failed")
		return e
	}

	r := &NginxAccessEvent{wrappedEvent: Wrap(e)}
	if err := json.Unmarshal(b, &r); err != nil {
		Logger.Warn().
			Err(err).
			Str("input", string(b)).
			Msg("json.Unmarshal failed")
		return e
	}

	return r
}

// Priority returns the syslog severity level of this event.
func (e *NginxAccessEvent) Priority() Priority {
	if e.StatusCode > 499 {
		return PriNotice
	}
	return PriInfo
}

// Message implements the [Event] interface.
func (e *NginxAccessEvent) Message() Message {
	return e
}

// Pairs returns ordered key-value pairs for message construction.
// In this case we return pairs in roughly combined log format
// ordering, which seems more natural than lexical sorting for
// viewing webserver access logs.
func (e *NginxAccessEvent) Pairs() iter.Seq2[string, any] {
	tls := e.TLSProto
	if tls == "" {
		tls = "none"
	}

	return func(yield func(string, any) bool) {
		for _, pair := range []struct {
			k string
			v any
		}{
			{"client", e.RemoteAddr},
			{"user", e.RemoteUser},
			{"method", e.Method},
			{"uri", e.RequestURI},
			{"proto", e.Proto},
			{"tls", tls},
			{"status", e.StatusCode},
			{"referer", e.Referer},
			{"user_agent", e.UserAgent},
			{"host", e.Host},
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
