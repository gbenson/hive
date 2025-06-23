package logging

import (
	"encoding/json"
	"maps"
	"strings"

	"golang.org/x/crypto/blake2b"
)

// Event represents a systemd journal entry plus address fields.
type Event struct {
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

	// All fields of a journal entry, less outlined address fields.
	Fields map[string]string `json:"fields"`
}

// Blake2b256Digest returns the string-encoded BLAKE2b-256 digest of
// Fields, including the address field timestamps systemd moved out
// of line: everything hive-log-forwarder read from the journal less
// the cursor which it drops before forwarding to save bytes.
func (e *Event) Blake2b256Digest() string {
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
