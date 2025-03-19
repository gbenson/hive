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
	conn *Conn
	amqp *amqp.Channel
}

// Close closes the channel.
func (ch *Channel) Close() error {
	return ch.amqp.Close()
}

type Consumer interface {
	// Consume consumes one message from the queue.
	Consume(ctx context.Context, m *Message) error
}

// ConsumeEvents starts an event consumer that runs until its context
// is cancelled.
func (ch *Channel) ConsumeEvents(
	ctx context.Context,
	routingKey string,
	consumer Consumer,
) error {
	exchange := hive.Exchange{
		Name:    routingKey,
		Kind:    "fanout",
		Durable: true,
	}
	if err := exchange.Declare(ch.amqp); err != nil {
		return err
	}

	consumerName := strings.ReplaceAll(util.ServiceName(), "-", ".")
	queue := hive.Queue{
		Name:       fmt.Sprintf("%s.%s", consumerName, routingKey),
		Durable:    true,
		DeadLetter: true,
	}
	if err := queue.Declare(ch.amqp); err != nil {
		return err
	}

	if err := queue.Bind(ch.amqp, &exchange, ""); err != nil {
		return err
	}

	deliveries, err := queue.Consume(ctx, ch.amqp)
	if err != nil {
		return err
	}

	go func() {
		log.Println("INFO: Consuming", queue.Name)
		for d := range deliveries {
			ch.consume(ctx, d, consumer)
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
func (ch *Channel) PublishEvent(
	ctx context.Context,
	routingKey string,
	event cloudevents.Event,
) error {
	messageBody, err := json.Marshal(event)
	if err != nil {
		return err
	}
	contentType := cloudevents.ApplicationCloudEventsJSON

	exchange := hive.Exchange{
		Name:    routingKey,
		Kind:    "fanout",
		Durable: true,
	}
	if err := exchange.Declare(ch.amqp); err != nil {
		return err
	}

	return exchange.Publish(ctx, ch.amqp, contentType, messageBody)
}
