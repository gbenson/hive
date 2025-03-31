package service

import (
	"context"
	"testing"
	"time"

	"gbenson.net/hive/messaging"
)

func TestReport(t *testing.T) {
	rsm := RestartMonitor{
		ConditionReport: ConditionReport{
			Condition: ConditionDubious,
			Messages:  []string{"guten", "tag"},
		},
		EventID: "hello!",
		Time:    time.Unix(1234567890, 0),
	}

	// Validate RestartMonitor.Report()
	ch := mockChannel{t, nil}
	rsm.Report(context.TODO(), &ch)

	if len(ch.Publishes) != 1 {
		expectFatal(t, len(ch.Publishes), 1)
	}

	p := ch.Publishes[0]
	expect(t, p.RoutingKey, "service.status.reports")
	got, _ := p.Event.(*RestartMonitor)
	expect(t, &rsm, got)

	// Validate RestartMonitor.MarshalEvent()
	e, err := messaging.MarshalEvent(&rsm)
	expectFatal(t, nil, err)

	expect(t, e.ID(), "hello!")
	expect(t, e.Source(), "https://gbenson.net/hive/services/service.test")
	expect(t, e.Type(), "net.gbenson.hive.service_status_report")
	expect(t, e.DataContentType(), "application/json")
	expect(t, e.Subject(), "service.test")
	expect(t, e.Time().Unix(), 1234567890)
}

type mockChannel struct {
	T         *testing.T
	Publishes []publish
}

type publish struct {
	RoutingKey string
	Event      any
}

func (c *mockChannel) PublishEvent(
	ctx context.Context,
	routingKey string,
	event any,
) error {
	c.Publishes = append(c.Publishes, publish{routingKey, event})
	return nil
}

func (c *mockChannel) ConsumeEvents(
	ctx context.Context,
	routingKey string,
	consumer messaging.Consumer,
) error {
	c.T.Fatal("consume: unexpected call")
	return nil
}

func (c *mockChannel) Close() error {
	c.T.Fatal("close: unexpected call")
	return nil
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
