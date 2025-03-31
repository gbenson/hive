package messaging

import (
	"context"
	"testing"
	"time"

	"github.com/google/uuid"
)

func TestEventCompletion(t *testing.T) {
	start := time.Now()

	e, err := MockPublish(context.TODO(), "incomplete.event.tests", NewEvent())
	expectFatal(t, err, nil)

	// Check ID, source, type and time were populated.
	eventID, err := uuid.Parse(e.ID())
	expectFatal(t, err, nil)
	expect(t, e.ID(), eventID.String())

	expect(t, e.Source(), "https://gbenson.net/hive/services/messaging.test")

	expect(t, e.Type(), "net.gbenson.hive.incomplete_event_test")

	if etime := e.Time(); etime.IsZero() {
		t.Errorf("e.Time() not set")
	} else if e.Time().Before(start) {
		t.Errorf("e.Time() before test start?")
	} else if time.Now().Before(e.Time()) {
		t.Errorf("e.Time() in future!")
	}
}

func expect[T comparable](t *testing.T, got, want T) {
	t.Helper()
	if got == want {
		return
	}
	t.Errorf("want: %v, got: %v", want, got)
}

func expectFatal[T comparable](t *testing.T, got, want T) {
	t.Helper()
	if got == want {
		return
	}
	t.Fatalf("want: %v, got: %v", want, got)
}
