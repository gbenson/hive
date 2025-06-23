package collector

import (
	"context"
	"errors"
	"os"
	"sync"
	"time"

	"gbenson.net/go/logger"
)

type cursor struct {
	log       *logger.Logger
	stateFile string
	value     string
	updateC   chan string
	updateErr error
	countdown *time.Timer
	mu        sync.Mutex
}

const DefaultSaveInterval = time.Minute

func newCursor(ctx context.Context, stateFile string) (*cursor, error) {
	b, err := os.ReadFile(stateFile)
	if err != nil && !os.IsNotExist(err) {
		return nil, err
	}
	s := string(b)

	log := logger.Ctx(ctx).With().
		Str("filename", stateFile).
		Logger()

	return &cursor{
		log:       &log,
		stateFile: stateFile,
		value:     s,
		updateC:   make(chan string),
	}, nil
}

func (c *cursor) GetValue() string {
	c.mu.Lock()
	defer c.mu.Unlock()

	return c.value
}

func (c *cursor) Update(s string) error {
	if err := c.updateErr; err != nil {
		return err
	} else if s == "" {
		// Writing an empty value to the channel is how we
		// synchronize closing the channel (i.e. don't let
		// user code do it!)
		return errors.New("nil cursor")
	}

	c.updateC <- s

	return nil
}

func (c *cursor) Close() (err error) {
	defer func() {
		pv := recover()
		if pv != nil {
			err = logger.NewRecoveredPanicError(pv)
		}
	}()

	c.updateC <- ""

	return
}

func (c *cursor) Run(ctx context.Context) error {
	defer c.save()

	for {
		select {
		case <-ctx.Done():
			ctx = context.Background() // only do this once...
			time.AfterFunc(15*time.Second, func() {
				c.log.Warn().
					Str("reason", "timeout exceeded").
					Msg("Forcing shutdown")
				close(c.updateC)
			})

		case value, ok := <-c.updateC:
			if !ok {
				c.log.Debug().Msg("Channel closed")
				return nil // channel closed
			} else if value == "" {
				c.log.Debug().Msg("Closing channel")
				close(c.updateC)
				continue
			}

			c.setValue(value)
		}
	}
}

func (c *cursor) setValue(s string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if s == c.value || s == "" {
		c.log.Debug().
			Str("old_value", c.value).
			Str("new_value", s).
			Msg("Not updating")

		return // unchanged or empty
	}

	c.value = s

	if c.countdown != nil {
		return // already counting down
	}

	c.log.Debug().Msg("Scheduling background write")
	c.countdown = time.AfterFunc(DefaultSaveInterval, c.save)
}

func (c *cursor) save() {
	s := c.GetValue()
	log := c.log.With().Str("value", s).Logger()
	if s == "" {
		log.Warn().Msg("Not writing")
		return
	}

	log.Debug().Msg("Writing")
	err := os.WriteFile(c.stateFile, []byte(s), 0600)

	c.mu.Lock()
	defer c.mu.Unlock()

	c.countdown = nil

	if err != nil {
		c.updateErr = err
	}
}
