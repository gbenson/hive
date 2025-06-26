// Package systemd manages systemd journal entries for Hive.
package systemd

import (
	"encoding/json"
	"maps"
	"strings"
	"time"

	"gbenson.net/hive/logging/event"
	"gbenson.net/hive/logging/internal"
	"gbenson.net/hive/messaging"
	"golang.org/x/crypto/blake2b"
)

// JournalEntry represents a systemd journal entry plus address fields.
type JournalEntry struct {
	// Digest of Fields plus the two timestamp address fields.
	Digest string `json:"digest,omitempty"`

	// systemd address fields that sdjournal moves out of line.
	// Both are in **microseconds** since the epoch.
	RealtimeTimestamp  uint64 `json:"realtime_usec" bson:"realtime_us"`
	MonotonicTimestamp uint64 `json:"monotonic_usec" bson:"monotonic_us"`

	// Hive collection and ingestion timestamps.
	// These are in **nanoseconds** since the epoch.
	CollectionTimestamp int64 `json:"collected_nsec,omitempty" bson:"hive_collect_time_ns"`
	IngestionTimestamp  int64 `json:"ingested_nsec,omitempty" bson:"hive_ingest_time_ns"`

	// All fields of a journal entry, less outlined address fields, as defined in
	// https://www.freedesktop.org/software/systemd/man/latest/systemd.journal-fields.html.
	// Note that fields prefixed with an underscore are systemd _trusted fields_
	// added by systemd on the originating host.  Note that it's _systemd_ doing
	// the trusting.
	Fields map[string]string `json:"fields"`
}

// Blake2b256Digest returns the string-encoded BLAKE2b-256 digest of
// Fields, including the address field timestamps systemd moved out
// of line: everything hive-log-forwarder read from the journal less
// the cursor which it drops before forwarding to save bytes.
func (e *JournalEntry) Blake2b256Digest() string {
	fields := maps.Clone(e.Fields) // shallow copy

	fields["__REALTIME_TIMESTAMP"] = utoa(e.RealtimeTimestamp)
	fields["__MONOTONIC_TIMESTAMP"] = utoa(e.MonotonicTimestamp)

	// N.B. json.Marshal sorts map keys, so this is canonical.
	data, err := json.Marshal(fields)
	if err != nil {
		panic(err) // shouldn't be possible
	}

	buf := blake2b.Sum256(data)
	return "BLAKE2b:" + strings.TrimRight(b64encode(buf[:]), "=")
}

// Command returns the name of the process this journal entry
// originates from.  Generally this will be the name you see
// in top, so mostly lowercase alphanumeric with the occasional
// random one in parentheses.
func (e *JournalEntry) Command() string {
	// Prefer the "_COMM" trusted field.
	if result := e.Fields["_COMM"]; result != "" {
		return result
	}

	// Fall back to the "SYSLOG_IDENTIFIER" compatibility field.
	return e.Fields["SYSLOG_IDENTIFIER"]
}

// ContainerName returns the name of the container the originating
// process is running in.  Docker sets this, maybe others too.
// Will be empty if the originating process isn't in a container,
// or if the originating process is in a container managed by an
// engine we don't yet handle.
func (e *JournalEntry) ContainerName() string {
	return e.Fields["CONTAINER_NAME"]
}

// Hostname returns the name of the originating host.
func (e *JournalEntry) Hostname() string {
	return e.Fields["_HOSTNAME"]
}

// Message returns the human-readable text of this entry, as
// supplied by the originating process.  It's supposed to be the
// primary text shown to the user.  Note that newline characters
// are permitted.  Expect to find ANSI control sequences too.
func (e *JournalEntry) Message() event.Message {
	return internal.UnstructuredMessage(e.Fields["MESSAGE"])
}

// Time returns the wallclock time of the originating host at the
// point in time the entry was received by the systemd journal.
// It has microsecond granularity.
func (e *JournalEntry) Time() time.Time {
	return time.UnixMicro(int64(e.RealtimeTimestamp))
}

// MarshalEvent implements the [messaging.EventMarshaler] interface.
func (e *JournalEntry) MarshalEvent() (*messaging.Event, error) {
	event := messaging.NewEvent()

	// Hoist the digest into the envelope.
	digest := e.Blake2b256Digest()
	switch e.Digest {
	case digest:
		e = clone(e)
		e.Digest = ""
		fallthrough
	case "":
		event.SetID(digest)
	default:
		return nil, &DigestError{Got: e.Digest, Want: digest}
	}

	// Hoist the collection timestamp into the envelope.
	if e.CollectionTimestamp != 0 {
		event.SetTime(time.Unix(0, e.CollectionTimestamp))
		e = clone(e)
		e.CollectionTimestamp = 0
	}

	event.SetData("application/json", e)

	return event, nil
}

// UnmarshalEvent unmarshals a [messaging.Event] into a [JournalEntry].
func UnmarshalEvent(e *messaging.Event) (*JournalEntry, error) {
	var entry JournalEntry
	if err := messaging.UnmarshalEvent(e, &entry); err != nil {
		return nil, err
	}
	return &entry, nil
}

// UnmarshalEvent implements the [messaging.EventUnarshaler] interface.
func (e *JournalEntry) UnmarshalEvent(event *messaging.Event) error {
	if err := event.DataAs(e); err != nil {
		return err
	}

	// Sink the collection timestamp and digest, if necessary.
	if e.CollectionTimestamp == 0 {
		e.CollectionTimestamp = event.Time().UnixNano()
	}
	if e.Digest == "" {
		e.Digest = event.ID()
	}

	return nil
}
