package service

import (
	"context"

	cloudevents "github.com/cloudevents/sdk-go/v2"

	"gbenson.net/hive/messaging"
)

type Channel struct {
	conn       *messaging.Conn
	pubc, conc *messaging.Channel
}

// Close closes the channel.
func (c *Channel) Close() error {
	if c.pubc != nil {
		defer c.pubc.Close()
	}
	if c.conc != nil {
		defer c.conc.Close()
	}
	return nil
}

// pc returns a messaging.Channel to use for publishing.
func (c *Channel) pc() (*messaging.Channel, error) {
	var err error
	if c.pubc == nil {
		c.pubc, err = c.conn.Channel()
	}
	return c.pubc, err
}

// cc returns a messaging.Channel to use for consuming.
func (c *Channel) cc() (*messaging.Channel, error) {
	var err error
	if c.pubc == nil {
		c.pubc, err = c.conn.Channel()
	}
	return c.pubc, err
}

// PublishEvent publishes an event to an exchange.
func (c *Channel) PublishEvent(
	ctx context.Context,
	routingKey string,
	event cloudevents.Event,
) error {
	ch, err := c.pc()
	if err != nil {
		return err
	}
	return ch.PublishEvent(ctx, routingKey, event)
}

// ConsumeEvents starts an event consumer that runs until its context
// is cancelled.
func (c *Channel) ConsumeEvents(
	ctx context.Context,
	routingKey string,
	consumer messaging.Consumer,
) error {
	ch, err := c.cc()
	if err != nil {
		return err
	}
	return ch.ConsumeEvents(ctx, routingKey, consumer)
}
