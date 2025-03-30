// Package service provides common code for Hive services.
package service

import (
	"context"
	"errors"
	"io"
	stdlog "log"
	"os"
	"os/signal"
	"syscall"

	"gbenson.net/hive/logger"
	"gbenson.net/hive/messaging"
	"gbenson.net/hive/util"
)

type Service interface {
	// Start starts the service's goroutines.
	Start(ctx context.Context, ch *messaging.Channel) error
}

// Run runs a Hive service.
func Run(s Service) {
	log := logger.New(&logger.Options{})
	RunContext(log.WithContext(context.Background()), s)
	log.Debug().Msg("Normal exit")
}

// RunContext runs a Hive service with the given context.
func RunContext(ctx context.Context, s Service) {
	if ctx == nil {
		panic("nil context")
	}

	if err := runContext(ctx, s); err != nil && err != context.Canceled {
		if !IsLoggedError(err) {
			logger.Ctx(ctx).Err(err).Msg("")
		}
		os.Exit(1)
	}
}

// Run a Hive service with the given context.  Note that errors and
// panics in startService are reported via the RestartMonitor: any
// code that *could* be in startService *should* be in startService.
func runContext(ctx context.Context, s Service) error {
	if stdlog.Flags() == stdlog.LstdFlags {
		stdlog.SetFlags(stdlog.Lshortfile)
	}

	// Create the restart monitor.
	rsm := NewRestartMonitor(ctx)

	// Connect to the message bus.
	conn, err := messaging.Dial(ctx)
	if err != nil {
		return err
	}
	defer conn.Close()

	ch, err := conn.Channel()
	if err != nil {
		return err
	}
	defer ch.Close()

	log := logger.Ctx(ctx)

	// Start the service's goroutines.
	if c, ok := s.(io.Closer); ok {
		defer log.Debug().Msg("Service stopped")
		defer func() {
			defer c.Close()
			log.Debug().Msg("Stopping service")
		}()
	}

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	if err := startService(ctx, s, rsm, ch); err != nil {
		return err
	}

	// Block until cancelled or interrupted.
	sigC := make(chan os.Signal, 1)
	signal.Notify(
		sigC,
		syscall.SIGHUP,
		syscall.SIGINT,
		syscall.SIGTERM,
	)

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case sig := <-sigC:
			signal.Reset() // Restore default handlers.
			log.Info().
				Str("reason", "signal").
				Str("signal", sig.String()).
				Msg("Shutting down")
			cancel()
		}
	}
}

// Start a Hive service.  Handles publishing the RestartMonitor report.
func startService(
	ctx context.Context,
	s Service,
	rsm *RestartMonitor,
	ch *messaging.Channel,
) (err error) {
	defer rsm.Report(ctx, ch)

	defer func() {
		pv := recover()
		if pv == nil {
			return
		}
		if err != nil && !IsLoggedError(err) {
			rsm.LogError(err)
		}
		err = util.NewRecoveredPanicError(pv)

		rsm.LogPanic(errors.Unwrap(err))
		err = &loggedError{err}
	}()

	if s == nil {
		panic("nil service")
	}

	defer func() {
		if err == nil {
			return
		}

		rsm.LogError(err)
		err = &loggedError{err}
	}()

	err = s.Start(ctx, ch)
	return
}
