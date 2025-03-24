// servicemonitor collates service condition reports into user messages.
package servicemonitor

import (
	"context"
	"encoding/json"
	"path/filepath"
	"time"

	bolt "go.etcd.io/bbolt"

	"gbenson.net/hive/logger"
	"gbenson.net/hive/messaging"
	"gbenson.net/hive/service"
)

// XXX document me
const Window = service.RapidRestartCutoff

// Service implements the [service.Service] interface.
type Service struct {
	db *bolt.DB
}

// Start starts the service's goroutines.
func (s *Service) Start(ctx context.Context, ch *messaging.Channel) error {
	statedir, err := service.StateDir()
	if err != nil {
		return err
	}
	database := filepath.Join(statedir, "state.db")

	logger.Ctx(ctx).Debug().
		Str("database", database).
		Msg("Opening")

	s.db, err = bolt.Open(database, 0600, nil)
	if err != nil {
		return err
	}
	if err = s.db.Update(ensureBuckets); err != nil {
		return err
	}

	return ch.ConsumeEvents(ctx, service.ConditionReportsQueue, s)
}

// Close releases any resources associated with the service.
func (s *Service) Close() error {
	if s.db == nil {
		return nil
	}
	return s.db.Close()
}

// Consume processes a service status report.
func (s *Service) Consume(ctx context.Context, m *messaging.Message) error {
	e, err := m.Event()
	if err != nil {
		return err
	}

	log := logger.Ctx(ctx)
	log.Debug().
		RawJSON("event", m.Body()).
		Msg("Received")

	r, err := ParseConditionReportEvent(&e)
	if err != nil {
		return err
	}

	if r.Time.IsZero() {
		log.Warn().
			RawJSON("event", m.Body()).
			Str("reason", "undated").
			Msg("Dropped")

		return nil
	}

	cutoff := time.Now().Add(-Window)
	if r.Time.Before(cutoff) {
		log.Warn().
			RawJSON("event", m.Body()).
			Time("time", r.Time).
			Time("cutoff", cutoff).
			Str("reason", "stale").
			Msg("Dropped")

		return nil
	}

	var prevstamp time.Time
	err = s.db.Update(func(tx *bolt.Tx) error {
		return processReport(tx, r.Service, r.Condition, r.Time, &prevstamp)
	})
	if err != nil {
		return err
	}

	if prevstamp.After(cutoff) {
		log.Debug().
			RawJSON("event", m.Body()).
			Time("last_seen", prevstamp).
			Time("cutoff", cutoff).
			Str("reason", "rate").
			Msg("Dropped")

		return nil
	}

	log.Info().
		Str("service", r.Service).
		Str("condition", r.Condition).
		Strs("messages", r.Messages).
		Msg("Service reported")

	req := r.AsTellUserRequest()

	if err := m.Channel().PublishEvent(ctx, "tell.user.requests", req); err != nil {
		return err
	}

	body, err := json.Marshal(req)
	if err != nil {
		log.Warn().
			Err(err).
			Msg("PublishEvent succeeded but json.Marshal(event) failed?")
		return nil
	}

	log.Debug().
		RawJSON("event", body).
		Msg("Published")

	return nil
}
