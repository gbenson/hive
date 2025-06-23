package logging

import (
	"maps"
	"slices"
	"testing"

	"go.mongodb.org/mongo-driver/v2/bson"
	"gotest.tools/v3/assert"
)

func newTestEvent() *Event {
	return &Event{
		RealtimeTimestamp:  1750582250015059,
		MonotonicTimestamp: 12829479768044,
		Fields: map[string]string{
			"MESSAGE":                     "veth9b80305: renamed from eth0",
			"PRIORITY":                    "6",
			"SYSLOG_FACILITY":             "0",
			"SYSLOG_IDENTIFIER":           "kernel",
			"_BOOT_ID":                    "27fbd0a3c26945e28624dad56044f8fe",
			"_HOSTNAME":                   "box1",
			"_MACHINE_ID":                 "b7ae3b30d3284b1dacb78ec9b966f531",
			"_SOURCE_MONOTONIC_TIMESTAMP": "12829697985567",
			"_TRANSPORT":                  "kernel",
		},
	}
}

// Marshalling to BSON results in the expected field names.
func TestMarshalBSON(t *testing.T) {
	b, err := bson.Marshal(newTestEvent())
	assert.NilError(t, err)

	var m map[string]any
	err = bson.Unmarshal(b, &m)
	assert.NilError(t, err)

	wantKeys := []string{
		"digest",
		"fields",
		"hive_collect_time_ns",
		"hive_ingest_time_ns",
		"monotonic_us",
		"realtime_us",
	}
	gotKeys := slices.Sorted(maps.Keys(m))
	assert.DeepEqual(t, gotKeys, wantKeys)
}

// TestBlake2b256Digest generates the correct digest.
func TestBlake2b256Digest(t *testing.T) {
	wantDigest := "BLAKE2b:XV8rVOrEXt3g4OX6sbbyynactnXVLFcFfmhNV8t7I2c"
	assert.Equal(t, newTestEvent().Blake2b256Digest(), wantDigest)
}
