package messaging

import (
	"errors"
	"strings"

	amqp "github.com/rabbitmq/amqp091-go"
)

type Message struct {
	d *amqp.Delivery
}

func (m *Message) Text() (string, error) {
	if m.d.ContentEncoding != "" ||
		!strings.HasPrefix(m.d.ContentType, "application/") ||
		!strings.HasSuffix(m.d.ContentType, "json") {
		return "", errors.New("not implemented")
	}

	return string(m.d.Body), nil
}
