package internal

import (
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
