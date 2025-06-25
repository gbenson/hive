package collector

import (
	"context"
	"maps"
	"slices"
	"testing"
	"time"

	"gbenson.net/hive/logging/systemd"
	"gbenson.net/hive/messaging"
	"github.com/coreos/go-systemd/v22/sdjournal"
	"gotest.tools/v3/assert"
)

func newTestEntry() *sdjournal.JournalEntry {
	return &sdjournal.JournalEntry{
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
		Cursor: "s=641988kg2wgurk;k=uapj5mz8zp7htndigu;g=uhs3ynj3kcf3r8xuz...",

		RealtimeTimestamp:  1750582250015059,
		MonotonicTimestamp: 12829479768044,
	}
}

func TestOnSerializedEntry(t *testing.T) {
	se, err := serializeEntry(newTestEntry())
	assert.NilError(t, err)

	ch := mockChannel{t: t}
	var ms Service
	start := time.Now()
	err = ms.onSerializedEntry(t.Context(), &ch, []byte(se))
	limit := time.Now()
	assert.NilError(t, err)
	e := ch.getPublishedEvent()

	// The event's ID should be the digest of the entry.
	assert.Equal(t, e.ID(), "BLAKE2b:XV8rVOrEXt3g4OX6sbbyynactnXVLFcFfmhNV8t7I2c")

	// The event's time should be between the start and end of the test.
	etime := e.Time()
	assert.Check(t, start.Before(etime))
	assert.Check(t, etime.Before(limit))

	// More specifically, the event's time should be right at the
	// start of the test, i.e. not set at the end by completeEvent.
	d1 := etime.Sub(start)
	d2 := limit.Sub(etime)
	assert.Check(t, d1 < d2)

	// The event's payload should only have fields and the two systemd
	// timestamps; the digest and collection time shouldn't be duplicated
	// from the envelope, and the cursor shouldn't be anywhere.
	var m map[string]any
	err = e.DataAs(&m)
	assert.NilError(t, err)
	wantKeys := []string{"fields", "monotonic_usec", "realtime_usec"}
	assert.DeepEqual(t, slices.Sorted(maps.Keys(m)), wantKeys)

	// The event should unmarshal correctly into a systemd.JournalEntry.
	// hive-log-ingester will fail if this doesn't work.
	entry, err := systemd.UnmarshalEvent(e)
	assert.NilError(t, err)

	assert.Equal(t, entry.RealtimeTimestamp, uint64(1750582250015059))
	assert.Equal(t, entry.MonotonicTimestamp, uint64(12829479768044))
	assert.Equal(t, entry.CollectionTimestamp, etime.UnixNano())

}

type mockChannel struct {
	t      *testing.T
	events []*messaging.Event
}

func (ch *mockChannel) PublishEvent(
	ctx context.Context,
	routingKey string,
	event any,
) error {
	t := ch.t
	t.Helper()

	assert.Equal(t, routingKey, "systemd.journal.events")

	e, err := messaging.MockPublish(ctx, routingKey, event)
	assert.NilError(t, err)
	ch.events = append(ch.events, e)

	return nil
}

func (ch *mockChannel) getPublishedEvent() *messaging.Event {
	t := ch.t
	t.Helper()
	assert.Equal(t, len(ch.events), 1)
	return ch.events[0]
}

func (ch *mockChannel) ConsumeEvents(
	ctx context.Context,
	routingKey string,
	c messaging.Consumer,
) error {
	panic("not implemented")
}

func (ch *mockChannel) ConsumeExclusive(
	ctx context.Context,
	routingKey string,
	c messaging.Consumer,
) error {
	panic("not implemented")
}

func (ch *mockChannel) Close() error {
	panic("not implemented")
}
