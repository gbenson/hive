package console

import (
	"context"
	"fmt"

	"gbenson.net/hive/logging"
	"gbenson.net/hive/messaging"
)

type Service struct {
	fmt Formatter
}

// Start starts the service's goroutines.
func (s *Service) Start(
	ctx context.Context,
	ch messaging.Channel,
) (<-chan error, error) {
	return nil, ch.ConsumeExclusive(ctx, logging.RawEventsQueue, s)
}

// Consume consumes one event.
func (s *Service) Consume(
	ctx context.Context,
	ch messaging.Channel,
	e *messaging.Event,
) error {
	var entry logging.Event
	if err := e.DataAs(&entry); err != nil {
		return err
	}

	fmt.Println(s.fmt.Format(&entry))
	return nil
}
