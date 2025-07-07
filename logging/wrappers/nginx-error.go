package wrappers

import (
	"fmt"
	"iter"
	"maps"
	"strings"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/wrappers/internal"

	"gbenson.net/hive/logging/internal/rxp"
	"gbenson.net/hive/logging/internal/rxparser"
)

// NginxErrorEvent represents an error_log event logged by Nginx.
type NginxErrorEvent struct {
	WrappedEvent
	fields map[string]any
}

// nginxErrorLogParser parses Nginx error log messages.
var nginxErrorLogParser = rxparser.MustCompile(rxp.NginxErrorLogEntry)

// nginxTrailingFieldRx parses a trailing field at the end of an
// Nginx error log message.
var nginxTrailingFieldParser = rxparser.MustCompile(rxp.NginxTrailingField)

// nginxErrorPairs declares which fields to omit from Pairs.
var nginxErrorPairs = OmitPairs("level", "time")

// nginxErrorPriorityMap maps Nginx error_log levels to syslog severity
// levels.  https://nginx.org/en/docs/ngx_core_module.html#error_log
var nginxErrorPriorityMap = PriorityMap{
	"debug":  PriDebug,
	"info":   PriInfo,
	"notice": PriNotice,
	"warn":   PriWarning,
	"error":  PriErr,
	"crit":   PriCrit,
	"alert":  PriAlert,
	"emerg":  PriEmerg,
}

// init registers an event modifier that returns a new NginxErrorEvent
// if the given event represents an error_log event logged by Nginx.
func init() {
	registerWrapper("nginx-error", func(e Event) Event {
		msg := e.Message()
		if len(msg.Fields()) > 0 {
			return e // already structured
		}

		fields := nginxErrorLogParser.ParseString(msg.String())
		if len(fields) < 2 {
			return e // no match
		}

		// Parse trailing fields from the end of fields["message"]
		// (e.g. ", client: 216.213.58.42, host: "gbenson.net").
		// Note that it's possible to mess with the quoting and get
		// e.g. `, host: "gbens"n,net"` though nginx and into the
		// logs, so we work on a copy and fail early if there's any
		// weirdness at all.
		if s, found := fields["message"]; found && s != "" {
			tmp := maps.Clone(fields)
			if err := popTrailers(tmp); err != nil {
				Logger.Warn().
					Err(err).
					Str("message", s).
					Msg("Unexpected trailers")
			} else {
				fields = tmp
			}
		}

		// Convert to map[string]any, dropping the unnamed match (the
		// entire string the regexp matched, which in this case is the
		// entire log entry).
		m := make(map[string]any)
		for k, v := range fields {
			if k == "" {
				continue
			}
			m[k] = v
		}

		return &NginxErrorEvent{Wrap(e), m}
	})
}

// popTrailers attempts to parse the trailing fields nginx appends to
// fields["message"] (e.g. `client: 216.213.58.42, host: "gbenson.net"`
// etc).  Note that it is possible to mess with the quoting and get
// e.g. `, host: "gbens"n,net"` though nginx and into the logs, so we
// fail early if we encounter *any* weirdness.
func popTrailers(fields map[string]string) error {
	s := fields["message"]
	for s != "" {
		r := nginxTrailingFieldParser.ParseString(s)
		if len(r) != 4 {
			break
		}

		k := r["key"]
		v := r["value"]

		v, found := strings.CutPrefix(v, `"`)
		if found {
			if v, found = strings.CutSuffix(v, `"`); !found {
				return fmt.Errorf(
					"weird trailing field %q in %q",
					r["value"],
					fields["message"],
				)
			}
		}

		if orig, found := fields[k]; found {
			return fmt.Errorf("%q <= %q would overwrite %q", k, v, orig)
		}

		fields[k] = v
		s = r["message"]
	}

	fields["message"] = s
	return nil
}

// Priority returns the syslog severity level of this event.
func (e *NginxErrorEvent) Priority() Priority {
	return nginxErrorPriorityMap.Get(Field(e, "level"))
}

// Message implements the [Event] interface.
func (e *NginxErrorEvent) Message() Message {
	return e
}

// Fields implements the [Message] interface.
func (e *NginxErrorEvent) Fields() map[string]any {
	return e.fields
}

// Pairs returns ordered key-value pairs for message construction.
func (e *NginxErrorEvent) Pairs() iter.Seq2[string, any] {
	return nginxErrorPairs(SortedPairs(e))
}
