// Package messaging provides messaging services for Hive.
package messaging

import "context"

// Conn is a connection to the Hive message bus.
type Conn interface {
	// Channel opens a channel for publishing and consuming messages.
	Channel() (Channel, error)

	// Close closes the connection.
	Close() error
}

// Channel is a channel for publishing and consuming messages.
type Channel interface {
	// ConsumeEvents starts an event consumer that runs until its
	// context is cancelled.
	ConsumeEvents(ctx context.Context, routingKey string, consumer Consumer) error

	// PublishEvent publishes an event.
	PublishEvent(ctx context.Context, routingKey string, event Event) error

	// Close closes the channel.
	Close() error
}

// Consumer is the interface that wraps the Consume method.
type Consumer interface {
	// Consume consumes one message from the queue.
	Consume(ctx context.Context, m *Message) error
}
