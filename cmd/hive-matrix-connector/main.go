// hive-matrix-connector is the Matrix connector service for Hive.
package main

import (
	"context"
	"log"

	"gbenson.net/hive/messaging"
	"gbenson.net/hive/service"
)

func main() {
	service.Run(&Service{})
}

type Service struct {
	cmc ChatMessageConsumer
}

func (s *Service) Start(ctx context.Context, ch *messaging.Channel) error {
	if err := ch.ConsumeEvents(ctx, "chat.messages", &s.cmc); err != nil {
		return err
	}

	return nil
}

type ChatMessageConsumer struct {
}

func (c *ChatMessageConsumer) Consume(
	ctx context.Context,
	m *messaging.Message,
) error {
	msg, err := m.Text()
	if err == nil {
		log.Println("INFO:", msg)
	}
	return err
}
