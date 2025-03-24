package messaging

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strings"

	cloudevents "github.com/cloudevents/sdk-go/v2"
	amqp "github.com/rabbitmq/amqp091-go"

	hive "gbenson.net/hive/messaging/internal"
	"gbenson.net/hive/util"
)

type Channel struct {
	conn       *Conn
	pubc, conc *amqp.Channel
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

// pc returns a amqp.Channel to use for publishing.
func (c *Channel) pc() (*amqp.Channel, error) {
	var err error
	if c.pubc == nil {
		c.pubc, err = c.newChannel()
	}
	return c.pubc, err
}

// cc returns a amqp.Channel to use for consuming.
func (c *Channel) cc() (*amqp.Channel, error) {
	var err error
	if c.pubc == nil {
		c.pubc, err = c.newChannel()
	}
	return c.pubc, err
}

func (c *Channel) newChannel() (*amqp.Channel, error) {
	ch, err := c.conn.amqp.Channel()
	if err != nil {
		return nil, err
	}

	// Don't let Publish fail silently.
	if err := ch.Confirm(false); err != nil {
		ch.Close()
		return nil, err
	}

	// Receive messages one at a time.
	if err := ch.Qos(1, 0, false); err != nil {
		ch.Close()
		return nil, err
	}

	return ch, nil
}

type Consumer interface {
	// Consume consumes one message from the queue.
	Consume(ctx context.Context, m *Message) error
}

// ConsumeEvents starts an event consumer that runs until its context
// is cancelled.
func (c *Channel) ConsumeEvents(
	ctx context.Context,
	routingKey string,
	consumer Consumer,
) error {
	ch, err := c.cc()
	if err != nil {
		return err
	}

	exchange := hive.Exchange{
		Name:    routingKey,
		Kind:    "fanout",
		Durable: true,
	}
	if err := exchange.Declare(ch); err != nil {
		return err
	}

	consumerName := strings.ReplaceAll(util.ServiceName(), "-", ".")
	queue := hive.Queue{
		Name:       fmt.Sprintf("%s.%s", consumerName, routingKey),
		Durable:    true,
		DeadLetter: true,
	}
	if err := queue.Declare(ch); err != nil {
		return err
	}

	if err := queue.Bind(ch, &exchange, ""); err != nil {
		return err
	}

	deliveries, err := queue.Consume(ctx, ch)
	if err != nil {
		return err
	}

	go func() {
		log.Println("INFO: Consuming", queue.Name)
		for d := range deliveries {
			c.consume(ctx, d, consumer)
		}
	}()

	return nil
}

func (ch *Channel) consume(ctx context.Context, d amqp.Delivery, c Consumer) {
	defer func() {
		if err := recover(); err != nil {
			d.Reject(false)
			log.Println("ERROR: panic:", err)
		}
	}()

	ctx, cancel := context.WithCancel(ctx) // XXX WithTimeout?
	defer cancel()

	switch err := c.Consume(ctx, &Message{&d}); err {
	case nil:
		d.Ack(false)
	default:
		d.Reject(false)
		log.Println("ERROR:", err)
	}
}

// PublishEvent publishes an event to an exchange.
func (c *Channel) PublishEvent(
	ctx context.Context,
	routingKey string,
	event cloudevents.Event,
) error {
	messageBody, err := json.Marshal(event)
	if err != nil {
		return err
	}
	contentType := cloudevents.ApplicationCloudEventsJSON

	ch, err := c.pc()
	if err != nil {
		return err
	}

	exchange := hive.Exchange{
		Name:    routingKey,
		Kind:    "fanout",
		Durable: true,
	}
	if err := exchange.Declare(ch); err != nil {
		return err
	}

	return exchange.Publish(ctx, ch, contentType, messageBody)
}
