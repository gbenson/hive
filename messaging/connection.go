package messaging

import (
	"context"
	"fmt"
	"time"

	amqp "github.com/rabbitmq/amqp091-go"

	"gbenson.net/go/logger"
	"gbenson.net/hive/config"
	"gbenson.net/hive/util"
)

// conn represents a connection to the Hive message bus.
// It implements the Conn interface.
type conn struct {
	amqp *amqp.Connection
	log  *logger.Logger
}

var rabbitConfigKeys = []string{
	"host",
	"port",
	"default_user",
	"default_pass",
}

// Dial returns a new connection to the Hive message bus.
func Dial(ctx context.Context) (Conn, error) {
	c := config.New("rabbitmq")

	uri, err := amqp.ParseURI("amqps:")
	if err != nil {
		return nil, err
	}

	c.SetDefault("host", "rabbit")
	c.SetDefault("port", uri.Port)

	for _, k := range rabbitConfigKeys {
		c.RegisterAlias(k, "rabbitmq_"+k)
	}

	if err := c.Read(); err != nil {
		return nil, err
	}

	uri.Host = c.GetString("host")
	uri.Port = c.GetInt("port")
	uri.Username = c.GetString("default_user")
	uri.Password = c.GetString("default_pass")

	return dial(ctx, fmt.Sprintf("%s?heartbeat=60", uri))
}

func dial(ctx context.Context, uri string) (Conn, error) {
	log := logger.Ctx(ctx).
		With().
		Str("uri", util.RedactURL(uri)).
		Logger()

	log.Debug().Msg("Dialling")

	c, err := amqp.Dial(uri)
	if err != nil {
		return nil, err
	}

	return &conn{c, &log}, nil
}

// ConnCloseTimeout is the maximum time [Conn.Close()] will wait
// for server acknowledgement.
const ConnCloseTimeout = 30 * time.Second

// Close closes the connection.
func (c *conn) Close() (err error) {
	return c.amqp.CloseDeadline(time.Now().Add(ConnCloseTimeout))
}

// Channel opens a channel for publishing and consuming messages.
func (c *conn) Channel() (Channel, error) {
	return &channel{conn: c}, nil
}

// closeChannel closes an AMQP channel.
func (c *conn) closeChannel(ch *amqp.Channel, name string) error {
	log := c.log.With().Str("kind", "consumer").Logger()
	logger.LoggedClose(&log, ch, "subchannel")
	return nil
}
