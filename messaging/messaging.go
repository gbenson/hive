// Package messaging provides messaging services for Hive.
package messaging

import "context"

// Conn is a connection to the Hive message bus.
type Conn interface {
	// Channel opens a channel for publishing and consuming messages.
	Channel() (Channel, error)

	// Close closes the connection.
	Close() error

	// NotifyClose registers a listener for close events either
	// initiated by an error accompanying a connection.close method
	// or by a normal shutdown.
	NotifyClose() <-chan error
}

// Channel is a channel for publishing and consuming messages.
type Channel interface {
	// ConsumeEvents starts an event consumer that runs until its
	// context is cancelled.
	ConsumeEvents(ctx context.Context, routingKey string, c Consumer) error

	// ConsumeExclusive works like ConsumeEvents but with a queue
	// which the broker will delete when the channel is closed.
	ConsumeExclusive(ctx context.Context, routingKey string, c Consumer) error

	// PublishEvent publishes an event.
	PublishEvent(ctx context.Context, routingKey string, event any) error

	// Close closes the channel.
	Close() error
}

// Consumer is the interface that wraps the Consume method.
type Consumer interface {
	// Consume consumes one event.
	Consume(ctx context.Context, c Channel, e *Event) error
}
