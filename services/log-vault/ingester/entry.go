package ingester

import (
	"encoding/json"
	"maps"
	"strings"

	"golang.org/x/crypto/blake2b"

	"go.mongodb.org/mongo-driver/v2/bson"
)

type JournalEntry struct {
	ID bson.ObjectID `bson:"_id"`

	// Digest of Fields plus the two timestamp address fields.
	Digest string `bson:"digest"`

	// systemd address fields sdjournal moves out of line.
	// Both are in **microseconds** since the epoch.
	RealtimeTimestamp  uint64 `bson:"realtime_us"`
	MonotonicTimestamp uint64 `bson:"monotonic_us"`

	// Hive collection and ingestion timestamps.
	// These are in **nanoseconds** since the epoch.
	CollectionTimestamp int64 `bson:"hive_collect_time_ns"`
	IngestionTimestamp  int64 `bson:"hive_ingest_time_ns"`

	// All fields of a journal entry, less outlined address fields.
	Fields map[string]string `bson:"fields"`
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
