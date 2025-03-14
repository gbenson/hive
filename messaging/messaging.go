// Package messaging provides messaging services for Hive.
package messaging

import (
	"fmt"

	amqp "github.com/rabbitmq/amqp091-go"

	"gbenson.net/hive/config"
)

type Conn struct {
	amqp *amqp.Connection
}

// Dial returns a new connection to the Hive message bus.
func Dial() (*Conn, error) {
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

	conn := &Conn{}
	conn.amqp, err = amqp.Dial(fmt.Sprintf("%s?heartbeat=600", uri))
	if err != nil {
		return nil, err
	}

	return conn, nil
}

// Close closes the connection.
func (c *Conn) Close() error {
	return c.amqp.Close()
}

// Channel opens a unique, concurrent channel to process messages.
func (c *Conn) Channel() (*Channel, error) {
	ch, err := c.amqp.Channel()
	if err != nil {
		return nil, err
	}

	// Don't let Publish fail silently.
	if err := ch.Confirm(false); err != nil {
		ch.Close()
		return nil, err
	}

	// Receive messages one at a time.
	if err := ch.Qos(1, 0, false); err != nil {
		ch.Close()
		return nil, err
	}

	return &Channel{c, ch}, nil
}
