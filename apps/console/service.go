package console

import (
	"context"
	"fmt"

	"gbenson.net/go/logger"
	"gbenson.net/hive/logging"
	"gbenson.net/hive/logging/sources/systemd"
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
	logging.Logger = logger.Ctx(ctx)
	return nil, ch.ConsumeExclusive(ctx, systemd.EventsQueue, s)
}

// Consume consumes one event.
func (s *Service) Consume(
	ctx context.Context,
	ch messaging.Channel,
	me *messaging.Event,
) error {
	le, err := logging.UnmarshalEvent(me)
	if err != nil {
		return err
	}

	fmt.Println(s.fmt.Format(le))
	return nil
}
