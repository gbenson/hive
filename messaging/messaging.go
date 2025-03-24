// Package messaging provides messaging services for Hive.
package messaging

import (
	"context"
	"fmt"

	amqp "github.com/rabbitmq/amqp091-go"

	"gbenson.net/hive/config"
	"gbenson.net/hive/logger"
	"gbenson.net/hive/util"
)

type Conn struct {
	amqp *amqp.Connection
	log  *logger.Logger
}

// Dial returns a new connection to the Hive message bus.
func Dial(ctx context.Context) (*Conn, error) {
	c := config.New("rabbitmq")

	uri, err := amqp.ParseURI("amqp:")
	if err != nil {
		return nil, err
	}

	c.SetDefault("host", "rabbit")
	c.SetDefault("port", uri.Port)

	c.RegisterAlias("default_user", "rabbitmq_default_user")
	c.RegisterAlias("default_pass", "rabbitmq_default_pass")

	if err := c.Read(); err != nil {
		return nil, err
	}

	uri.Host = c.GetString("host")
	uri.Port = c.GetInt("port")
	uri.Username = c.GetString("default_user")
	uri.Password = c.GetString("default_pass")

	return dial(ctx, fmt.Sprintf("%s?heartbeat=600", uri))
}

func dial(ctx context.Context, uri string) (*Conn, error) {
	log := logger.Ctx(ctx).
		With().
		Str("uri", util.RedactURL(uri)).
		Logger()

	log.Debug().Msg("Dialling")

	conn, err := amqp.Dial(uri)
	if err != nil {
		return nil, err
	}

	return &Conn{conn, &log}, nil
}

// Close closes the connection.
func (c *Conn) Close() error {
	defer c.amqp.Close()

	c.log.Debug().Msg("Closing message bus connection")

	return nil
}

// Channel opens a unique, concurrent channel to process messages.
func (c *Conn) Channel() (*Channel, error) {
	return &Channel{conn: c}, nil
}

// closeChannel closes an AMQP channel.
func (c *Conn) closeChannel(ch *amqp.Channel, name string) error {
	defer ch.Close()

	c.log.Debug().Str("channel", name).Msg("Closing messaging channel")

	return nil
}
