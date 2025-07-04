package systemd

import (
	"encoding/json"
	"maps"
	"strconv"
	"strings"
	"time"

	"golang.org/x/crypto/blake2b"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/internal"
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
// of line: everything the log collector read from the journal except
// the cursor which is dropped before forwarding.
func (e *JournalEntry) Blake2b256Digest() string {
	fields := maps.Clone(e.Fields) // shallow copy

	fields["__REALTIME_TIMESTAMP"] = utoa(e.RealtimeTimestamp)
	fields["__MONOTONIC_TIMESTAMP"] = utoa(e.MonotonicTimestamp)

	// N.B. json.Marshal sorts map keys, so this is canonical.
	data, err := json.Marshal(fields)
	if err != nil {
		panic(err) // shouldn't be possible, its a map[string]string...
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
func (e *JournalEntry) Message() Message {
	return UnstructuredMessage(e.Fields["MESSAGE"])
}

// Priority returns the RFC 5424 syslog severity level of this event,
// as reported by the originating process.  This isn't always present
// or useful, e.g. entries from processes in Docker containers are
// reported as PriInfo if collected from stdout or PriErr if reported
// on stderr, so the reported priority may well not line up with the
// content of the message.
func (e *JournalEntry) Priority() Priority {
	v, err := strconv.Atoi(e.Fields["PRIORITY"])
	if err != nil {
		return PriUnknown
	}

	p := Priority(v)
	if p < PriEmerg || p > PriDebug {
		return PriUnknown
	}

	return p
}

// Time returns the wallclock time of the originating host at the
// point in time the entry was received by the systemd journal.
// It has microsecond granularity.
func (e *JournalEntry) Time() time.Time {
	return time.UnixMicro(int64(e.RealtimeTimestamp))
}
