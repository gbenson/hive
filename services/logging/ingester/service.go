package ingester

import (
	"context"
	"errors"
	"time"

	"go.mongodb.org/mongo-driver/v2/mongo"

	"gbenson.net/go/logger"
	"gbenson.net/hive/logging/sources/systemd"
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

	return errC, ch.ConsumeEvents(ctx, systemd.EventsQueue, s)
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

	entry, err := systemd.UnmarshalEvent(event)
	if err != nil {
		return err
	}

	if entry.CollectionTimestamp < 1 {
		return errors.New("invalid collection timestamp")
	}

	if entry.IngestionTimestamp != 0 {
		return errors.New("unexpected ingestion timestamp")
	}
	entry.IngestionTimestamp = ingestionTime.UnixNano()

	wantDigest := entry.Blake2b256Digest()
	if entry.Digest != wantDigest {
		return &systemd.DigestError{Got: entry.Digest, Want: wantDigest}
	}

	_, err = s.db.Collection.InsertOne(ctx, entry)
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
