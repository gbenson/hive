package messaging

import (
	"bytes"
	"context"
	"fmt"
	"time"

	"github.com/cloudevents/sdk-go/v2/event"
	amqp "github.com/rabbitmq/amqp091-go"

	"gbenson.net/go/logger"
	"gbenson.net/hive/util"
)

// ConsumeTimeout is the maximum duration a [Consumer.Consume] may
// execute for before its context will be canceled.  RabbitMQ will
// stop waiting for the delivery acknowledgement after whatever its
// "consumer-timeout" is set to (the default is 30 minutes) so this
// value should probably be less than that.
const ConsumeTimeout = 5 * time.Minute

// ChannelContextKey is a context key. It can be used in consumers
// with Context.Value to access the channel that received the message
// being consumed. The associated value will be of type Channel.
var ChannelContextKey = util.NewContextKey("hive messaging-channel")

// consume manages the consumption of one message by a consumer.
func consume(ctx context.Context, ch Channel, d *amqp.Delivery, c Consumer) {
	var err error

	defer func() {
		defer ackOrReject(ctx, d, err == nil)
		if err != nil {
			logger.Ctx(ctx).
				WithLevel(logger.LevelFor(err)).
				Err(err).
				Msg("")
		}
	}()

	defer func() {
		pv := recover()
		if pv == nil {
			return
		}
		if err != nil {
			logger.Ctx(ctx).Err(err).Msg("")
		}
		err = logger.NewRecoveredPanicError(pv)
	}()

	var e Event
	if err = unmarshalForConsume(&e, d); err != nil {
		return
	}

	log := logger.Ctx(ctx)
	log.Debug().
		RawJSON("event", d.Body).
		Msg("Received")

	ctx, cancel := context.WithTimeout(ctx, ConsumeTimeout)
	defer cancel()

	err = c.Consume(ctx, ch, &e)
}

func unmarshalForConsume(e *Event, d *amqp.Delivery) error {
	if d.ContentType != ApplicationCloudEventsJSON {
		return fmt.Errorf("unexpected content type %q", d.ContentType)
	}

	return event.ReadJson(e, bytes.NewReader(d.Body))
}

func ackOrReject(ctx context.Context, d *amqp.Delivery, ok bool) {
	var err error
	if ok {
		err = d.Ack(false)
	} else {
		err = d.Reject(false)
	}
	if err == nil {
		return
	}
	logger.Ctx(ctx).Err(err).Msg("")
}
