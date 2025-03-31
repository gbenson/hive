package messaging

import (
	"bytes"
	"fmt"

	"github.com/cloudevents/sdk-go/v2/event"
	amqp "github.com/rabbitmq/amqp091-go"
)

type Message struct {
	d  *amqp.Delivery
	ch *channel
}

// Channel returns the channel this message was consumed from.
func (m *Message) Channel() Channel {
	return m.ch
}

// Body returns the raw bytes of the message body.
func (m *Message) Body() []byte {
	return m.d.Body
}

// Event parses the message as a CloudEvent.
func (m *Message) Event() (e Event, err error) {
	if m.d.ContentType != ApplicationCloudEventsJSON {
		err = fmt.Errorf("unexpected content type %q", m.d.ContentType)
	} else {
		err = event.ReadJson(&e, bytes.NewReader(m.Body()))
	}
	return
}
