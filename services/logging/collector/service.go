package collector

import (
	"context"
	"encoding/json"
	"path/filepath"
	"sync"
	"time"

	"github.com/coreos/go-systemd/v22/sdjournal"

	"gbenson.net/go/logger"
	"gbenson.net/hive/logging"
	"gbenson.net/hive/messaging"
	"gbenson.net/hive/util"

	"gbenson.net/hive/services/logging/collector/filters"
)

const DefaultBacklog = time.Minute

type Service struct {
	log      *logger.Logger
	cm       *cursor
	stopChan chan time.Time
	stopWait sync.WaitGroup
}

func (s *Service) Start(
	ctx context.Context,
	ch messaging.Channel,
) (<-chan error, error) {
	s.log = logger.Ctx(ctx)

	stateDir, err := util.ServiceStateDir()
	if err != nil {
		return nil, err
	}

	s.cm, err = newCursor(ctx, filepath.Join(stateDir, "cursor"))
	if err != nil {
		return nil, err
	}

	rc := sdjournal.JournalReaderConfig{
		Cursor:    s.cm.GetValue(),
		Formatter: serializeEntry,
	}
	if rc.Cursor == "" {
		rc.Since = -DefaultBacklog
		s.cm.log.Debug().
			Dur("since", rc.Since).
			Msg("No cursor, will spool recent entries")
	} else {
		s.cm.log.Debug().
			Str("value", rc.Cursor).
			Msg("Got cursor")
	}

	r, err := sdjournal.NewJournalReader(rc)
	if err != nil {
		return nil, err
	}

	w := serializedEntryReceiver{ctx, ch, s}

	errC := make(chan error, 2)
	s.stopChan = make(chan time.Time)

	s.stopWait.Add(1)
	go func() {
		defer s.stopWait.Done()
		defer logger.LoggedClose(s.log, s.cm, "cursor manager")

		s.log.Debug().Msg("Starting journal reader")

		err := r.Follow(s.stopChan, &w)

		s.log.Debug().Err(err).Msg("JournalReader.Follow returned")
		errC <- err
		s.log.Debug().Err(err).Msg("Journal reader stopping")
	}()

	s.stopWait.Add(1)
	go func() {
		defer s.stopWait.Done()

		s.log.Debug().Msg("Starting cursor manager")

		err := s.cm.Run(ctx)

		s.log.Debug().Err(err).Msg("CursorManager.Run returned")
		errC <- err
		s.log.Debug().Msg("Cursor manager stopping")
	}()

	return errC, nil
}

func (s *Service) Close() error {
	if s.stopChan == nil {
		return nil
	}

	s.log.Debug().Msg("Stopping journal reader")
	close(s.stopChan)
	s.log.Debug().Msg("Waiting for journal reader to stop")
	s.stopWait.Wait()
	s.log.Debug().Msg("Journal reader stopped")

	return nil
}

func serializeEntry(entry *sdjournal.JournalEntry) (string, error) {
	b, err := json.Marshal(entry)
	if err != nil {
		return "", err
	}
	return string(b), nil
}

type serializedEntryReceiver struct {
	ctx     context.Context
	ch      messaging.Channel
	service *Service
}

func (r *serializedEntryReceiver) Write(b []byte) (n int, err error) {
	if err := r.service.onSerializedEntry(r.ctx, r.ch, b); err != nil {
		return 0, err
	}
	return len(b), nil
}

func (s *Service) onSerializedEntry(
	ctx context.Context,
	ch messaging.Channel,
	b []byte,
) error {
	collectionTime := time.Now()

	if err := ctx.Err(); err != nil {
		return err
	}

	var entry sdjournal.JournalEntry
	if err := json.Unmarshal(b, &entry); err != nil {
		return err
	}

	if filters.ShouldForwardEvent(entry.Fields) {
		payload := logging.Event{
			Fields:             entry.Fields,
			RealtimeTimestamp:  entry.RealtimeTimestamp,
			MonotonicTimestamp: entry.MonotonicTimestamp,
		}
		event := messaging.NewEvent()

		event.SetID(payload.Blake2b256Digest())
		event.SetTime(collectionTime)
		event.SetData("application/json", payload)

		if err := ch.PublishEvent(ctx, logging.RawEventsQueue, event); err != nil {
			return err
		}
	}

	var err error
	if s.cm != nil {
		err = s.cm.Update(entry.Cursor)
	}
	return err
}
