package messaging

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	amqp "github.com/rabbitmq/amqp091-go"

	"gbenson.net/go/logger"
	hive "gbenson.net/hive/messaging/internal"
	"gbenson.net/hive/util"
)

type channel struct {
	conn       *conn
	pubc, conc *amqp.Channel
}

// Close closes the channel.
func (c *channel) Close() error {
	if c.pubc != nil {
		defer c.conn.closeChannel(c.pubc, "publisher")
	}
	if c.conc != nil {
		defer c.conn.closeChannel(c.conc, "consumer")
	}
	return nil
}

// publishChannel returns an amqp.Channel to use for publishing.
func (c *channel) publishChannel() (ch *amqp.Channel, err error) {
	if ch = c.pubc; ch != nil {
		return
	} else if ch, err = c.conn.amqp.Channel(); err != nil {
		return nil, err
	}

	// Don't let Publish fail silently.
	if err = ch.Confirm(false); err != nil {
		defer ch.Close()
		return nil, err
	}

	c.pubc = ch
	return ch, nil
}

// consumeChannel returns an amqp.Channel to use for consuming.
func (c *channel) consumeChannel() (ch *amqp.Channel, err error) {
	if ch = c.conc; ch != nil {
		return
	} else if ch, err = c.conn.amqp.Channel(); err != nil {
		return nil, err
	}

	// Receive messages one at a time.
	if err = ch.Qos(1, 0, false); err != nil {
		defer ch.Close()
		return nil, err
	}

	c.conc = ch
	return ch, nil
}

// ConsumeEvents starts an event consumer that runs until its context
// is cancelled.
func (c *channel) ConsumeEvents(
	ctx context.Context,
	routingKey string,
	consumer Consumer,
) error {
	ch, err := c.consumeChannel()
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
		logger.Ctx(ctx).Info().
			Str("route", routingKey). // where you publish
			Str("queue", queue.Name). // what we're consuming
			Msg("Consuming events")

		for d := range deliveries {
			consume(ctx, c, &d, consumer)
		}
	}()

	return nil
}

// PublishEvent publishes an event.
func (c *channel) PublishEvent(
	ctx context.Context,
	routingKey string,
	event any,
) error {
	contentType, messageBody, err := marshalForPublish(event, routingKey)
	if err != nil {
		return err
	}

	ch, err := c.publishChannel()
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

func marshalForPublish(event any, routingKey string) (string, []byte, error) {
	e, err := MarshalEvent(event)
	if err != nil {
		return "", nil, err
	}

	if err := completeEvent(e, routingKey); err != nil {
		return "", nil, err
	}

	if err := e.Validate(); err != nil {
		return "", nil, err
	}

	messageBody, err := json.Marshal(e)
	if err != nil {
		return "", nil, err
	}

	return ApplicationCloudEventsJSON, messageBody, nil
}

// MockPublish marshals the given event like PublishEvent, then
// unmarshals it back to an event.
func MockPublish(ctx context.Context, routingKey string, e any) (*Event, error) {
	ct, body, err := marshalForPublish(e, routingKey)
	if err != nil {
		return nil, err
	}
	d := amqp.Delivery{
		ContentType: ct,
		Body:        body,
	}
	var result Event
	if err := unmarshalForConsume(&result, &d); err != nil {
		return nil, err
	}
	return &result, nil
}
