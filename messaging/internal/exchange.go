package internal

import (
	"context"
	"fmt"

	amqp "github.com/rabbitmq/amqp091-go"
)

type Exchange struct {
	Name    string
	Kind    string
	Durable bool
}

func (e *Exchange) amqpName() string {
	return fmt.Sprintf("hive.%s", e.Name)
}

func (e *Exchange) Declare(ch *amqp.Channel) error {
	return ch.ExchangeDeclare(
		e.amqpName(), // name
		e.Kind,       // type
		e.Durable,    // durable
		false,        // auto-deleted
		false,        // internal
		false,        // no-wait
		nil,          // arguments
	)
}

func (e *Exchange) Publish(
	ctx context.Context,
	ch *amqp.Channel,
	contentType string,
	body []byte,
) error {
	// "Add a listener with Channel.NotifyReturn to handle any undeliverable
	// message when calling publish with either the mandatory or immediate
	// parameters as true."
	// https://pkg.go.dev/github.com/rabbitmq/amqp091-go#Channel.PublishWithContext
	return ch.PublishWithContext(
		ctx,          // context
		e.amqpName(), // exchange
		"",           // routing key
		false,        // mandatory
		false,        // immediate
		amqp.Publishing{
			ContentType: contentType,
			Body:        body,
		},
	)
}
