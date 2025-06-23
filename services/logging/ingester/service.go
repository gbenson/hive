package ingester

import (
	"context"
	"time"

	"github.com/coreos/go-systemd/v22/sdjournal"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"

	"gbenson.net/go/logger"
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

	return errC, ch.ConsumeEvents(ctx, "systemd.journald.events", s)
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

	var se sdjournal.JournalEntry
	if err := event.DataAs(&se); err != nil {
		return err
	}

	entry := JournalEntry{
		ID:                  bson.NewObjectID(),
		Fields:              se.Fields,
		RealtimeTimestamp:   se.RealtimeTimestamp,
		MonotonicTimestamp:  se.MonotonicTimestamp,
		CollectionTimestamp: event.Time().UnixNano(),
		IngestionTimestamp:  ingestionTime.UnixNano(),
	}
	entry.Digest = entry.Blake2b256Digest()

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
