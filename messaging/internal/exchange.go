package internal

import (
	"context"
	"fmt"
	"sync"

	amqp "github.com/rabbitmq/amqp091-go"

	"gbenson.net/go/logger"
)

type Exchange struct {
	Name    string
	Kind    string
	Durable bool

	mu       sync.Mutex
	amqpName string
}

func (e *Exchange) Declare(ctx context.Context, ch *amqp.Channel) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	e.amqpName = fmt.Sprintf("hive.%s", e.Name)

	logger.Ctx(ctx).Debug().
		Str("name", e.amqpName).
		Msg("Declaring exchange")

	return ch.ExchangeDeclare(
		e.amqpName, // name
		e.Kind,     // type
		e.Durable,  // durable
		false,      // auto-deleted
		false,      // internal
		false,      // no-wait
		nil,        // arguments
	)
}

func (e *Exchange) Publish(
	ctx context.Context,
	ch *amqp.Channel,
	contentType string,
	body []byte,
) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	// "Add a listener with Channel.NotifyReturn to handle any undeliverable
	// message when calling publish with either the mandatory or immediate
	// parameters as true."
	// https://pkg.go.dev/github.com/rabbitmq/amqp091-go#Channel.PublishWithContext
	return ch.PublishWithContext(
		ctx,        // context
		e.amqpName, // exchange
		"",         // routing key
		false,      // mandatory
		false,      // immediate
		amqp.Publishing{
			ContentType: contentType,
			Body:        body,
		},
	)
}
