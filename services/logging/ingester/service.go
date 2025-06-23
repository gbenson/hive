package ingester

import (
	"context"
	"fmt"
	"time"

	"go.mongodb.org/mongo-driver/v2/mongo"

	"gbenson.net/go/logger"
	"gbenson.net/hive/logging"
	"gbenson.net/hive/messaging"
)

type Service struct {
	log  *logger.Logger
	db   *Client
	errC chan<- error
}

// Start starts the service's goroutines.
func (s *Service) Start(
	ctx context.Context,
	ch messaging.Channel,
) (<-chan error, error) {
	s.log = logger.Ctx(ctx)

	if db, err := Dial(ctx); err != nil {
		return nil, err
	} else {
		s.db = db
	}

	errC := make(chan error)
	s.errC = errC

	return errC, ch.ConsumeEvents(ctx, logging.RawEventsQueue, s)
}

// Close shuts down the service.
func (s *Service) Close() error {
	if s.db == nil {
		return nil
	}

	logger.LoggedClose(s.log, s.db, "database connection")

	return nil
}

// Consume consumes one event.
func (s *Service) Consume(
	ctx context.Context,
	ch messaging.Channel,
	event *messaging.Event,
) error {
	ingestionTime := time.Now()

	var entry logging.Event
	if err := event.DataAs(&entry); err != nil {
		return err
	}

	if entry.CollectionTimestamp != 0 {
		s.log.Warn().
			Str("field", "CollectionTimestamp").
			Int64("value", entry.CollectionTimestamp).
			Msg("Overwriting")
	}
	entry.CollectionTimestamp = event.Time().UnixNano()

	if entry.IngestionTimestamp != 0 {
		s.log.Warn().
			Str("field", "IngestionTimestamp").
			Int64("value", entry.IngestionTimestamp).
			Msg("Overwriting")
	}
	entry.IngestionTimestamp = ingestionTime.UnixNano()

	if entry.Digest != "" {
		s.log.Warn().
			Str("field", "Digest").
			Str("value", entry.Digest).
			Msg("Overwriting")
	}
	entry.Digest = event.ID()
	wantDigest := entry.Blake2b256Digest()

	if entry.Digest != wantDigest {
		return fmt.Errorf("%q != %q", wantDigest, entry.Digest)
	}

	_, err := s.db.Collection.InsertOne(ctx, entry)
	if err != nil {
		if !mongo.IsDuplicateKeyError(err) {
			return err
		}

		s.log.Warn().
			Str("action", "dropped").
			Str("event_id", event.ID()).
			Time("event_time", event.Time()).
			Uint64("realtime_timestamp", entry.RealtimeTimestamp).
			Msg("Duplicate")

		return nil
	}

	return nil
}
