package forwarder

import (
	"context"
	"encoding/json"
	"maps"
	"regexp"
	"strings"
	"time"

	"gbenson.net/go/logger"
	"gbenson.net/hive/messaging"
)

// InputRecord is a raw event received from logspout, which emits
// them formatted per the RAW_FORMAT environment variable specified
// in its docker-compose.yml.
type InputRecord struct {
	// Values read from logspout.
	Timestamp time.Time `json:"t"`
	Hostname  string    `json:"h"`
	Container string    `json:"c"` // Docker internal, so with leading "/".
	Stream    string    `json:"s"` // logspout source: "stdout" or "stderr".
	Message   string    `json:"m"`

	// Values added by us.
	RunID    string `json:"-"` // UUID of this log-forwarder run.
	Sequence uint64 `json:"-"` // Order this record was received.
}

type OutputRecord struct {
	RunID     string `json:"run"` // UUID of this log-forwarder run.
	Sequence  uint64 `json:"seq"` // Order this record was received.
	Hostname  string `json:"host"`
	Container string `json:"container"`        // Leading "/" removed
	Stream    string `json:"stream,omitempty"` // "stdout" or "stderr" for generic.
	Message   any    `json:"message"`          // string for generic, mapping for nginx
}

func (r *InputRecord) Forward(ctx context.Context, ch messaging.Channel) error {
	if strings.HasPrefix(r.Container, "/hive-nginx-") {
		return r.forwardNginx(ctx, ch)
	}

	return r.forwardGeneric(ctx, ch)
}

// Forward a repackaged but otherwise unmodified version of the input record.
func (r *InputRecord) forwardGeneric(
	ctx context.Context,
	ch messaging.Channel,
) error {
	return ch.PublishEvent(ctx, "logspout.events", r)
}

func (r *InputRecord) MarshalEvent() (*messaging.Event, error) {
	e := messaging.NewEvent()
	e.SetTime(r.Timestamp)
	e.SetData("application/json", &OutputRecord{
		RunID:     r.RunID,
		Sequence:  r.Sequence,
		Hostname:  r.Hostname,
		Container: strings.TrimPrefix(r.Container, "/"),
		Stream:    r.Stream,
		Message:   r.Message,
	})
	return e, nil
}

type notHandled struct{}

func (e *notHandled) Error() string {
	return "not handled"
}

var NotHandled = &notHandled{}

func (r *InputRecord) forwardNginx(
	ctx context.Context,
	ch messaging.Channel,
) error {
	switch r.Stream {
	case "stderr":
		if err := r.forwardNginxError(ctx, ch); err != NotHandled {
			return err
		}
	case "stdout":
		if err := r.forwardNginxAccess(ctx, ch); err != NotHandled {
			return err
		}
	}

	return r.forwardGeneric(ctx, ch)
}

var notFoundRx = regexp.MustCompile(
	`"/(?:usr/share/nginx/html|var/www/letsencrypt)/[^"]*"` +
		` (?:failed|is not found)` +
		` \(2: No such file or directory\)`,
)

// forwardNginxError drops some noisy messages, forwarding everything
// else as generic records.
func (r *InputRecord) forwardNginxError(
	ctx context.Context,
	ch messaging.Channel,
) error {
	dt, msg, found := strings.Cut(r.Message, " [")
	if !found {
		return NotHandled
	}
	level, msg, found := strings.Cut(msg, "] ")
	if !found {
		return NotHandled
	}

	switch level {
	case "error":
		if notFoundRx.MatchString(msg) {
			logger.Ctx(ctx).Trace().
				Str("_datetime", dt).
				Str("_level", level).
				Str("_message", msg).
				Msg("Dropped")

			return nil
		}
	case "warn":
		if strings.Contains(msg, " is buffered to a temporary file ") {
			logger.Ctx(ctx).Trace().
				Str("_datetime", dt).
				Str("_level", level).
				Str("_message", msg).
				Msg("Dropped")

			return nil
		}
	}

	return NotHandled
}

// forwardNginxAccess reroutes nginx access logs to their own queue.
func (r *InputRecord) forwardNginxAccess(
	ctx context.Context,
	ch messaging.Channel,
) error {
	var m map[string]any

	if err := json.Unmarshal([]byte(r.Message), &m); err != nil {
		logger.Ctx(ctx).Warn().Err(err).Msg("Malformed JSON")
		return NotHandled
	}

	// Delete any key whose value is the empty string.
	maps.DeleteFunc(m, func(k string, v any) bool {
		vv, ok := v.(string)
		return ok && vv == ""
	})

	// Wrap the record in a cloudevent.
	e := messaging.NewEvent()
	e.SetTime(r.Timestamp)
	e.SetData("application/json", &OutputRecord{
		RunID:     r.RunID,
		Sequence:  r.Sequence,
		Hostname:  r.Hostname,
		Container: strings.TrimPrefix(r.Container, "/"),
		Message:   m,
	})

	return ch.PublishEvent(ctx, "nginx.access.events", e)
}
