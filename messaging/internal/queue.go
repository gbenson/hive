package internal

import (
	"context"
	"fmt"

	amqp "github.com/rabbitmq/amqp091-go"

	"gbenson.net/go/logger"
)

type Queue struct {
	Name       string
	Durable    bool
	DeadLetter bool
	Exclusive  bool
}

func (q *Queue) Declare(ctx context.Context, ch *amqp.Channel) error {
	var args amqp.Table

	if q.DeadLetter {
		dlx := Exchange{
			Name:    "dead.letter",
			Kind:    "direct",
			Durable: true,
		}
		if err := dlx.Declare(ctx, ch); err != nil {
			return err
		}

		dlq := Queue{
			Name:    fmt.Sprintf("x.%s", q.Name),
			Durable: true,
		}
		if err := dlq.Declare(ctx, ch); err != nil {
			return err
		}

		if err := dlq.Bind(ch, &dlx, q.Name); err != nil {
			return err
		}

		args = amqp.Table{
			"x-dead-letter-exchange": dlx.amqpName,
		}
	}

	logger.Ctx(ctx).Debug().
		Str("name", q.Name).
		Msg("Declaring queue")

	declaredQueue, err := ch.QueueDeclare(
		q.Name,      // name
		q.Durable,   // durable
		false,       // delete when unused
		q.Exclusive, // exclusive
		false,       // no-wait
		args,
	)
	if err != nil {
		return nil
	}

	q.Name = declaredQueue.Name
	return nil
}

func (q *Queue) Bind(ch *amqp.Channel, e *Exchange, routingKey string) error {
	return ch.QueueBind(q.Name, routingKey, e.amqpName, false, nil)
}

func (q *Queue) Consume(
	ctx context.Context, ch *amqp.Channel) (<-chan amqp.Delivery, error) {

	return ch.ConsumeWithContext(
		ctx,    // context
		q.Name, // queue
		"",     // consumer name
		false,  // auto ack
		false,  // exclusive
		false,  // no local
		false,  // no wait
		nil,    // args
	)
}
