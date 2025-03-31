// Package hive provides common code for Hive services.
package hive

import (
	"context"
	"io"
	stdlog "log"
	"os"
	"os/signal"
	"syscall"

	"gbenson.net/hive/logger"
	"gbenson.net/hive/messaging"
)

type Service interface {
	// Start starts the service's goroutines.
	Start(ctx context.Context, ch messaging.Channel) error
}

// Run runs a Hive service.
func Run(s Service) {
	log := logger.New(&logger.Options{})
	RunContext(log.WithContext(context.Background()), s)
}

// RunContext runs a Hive service with the given context.
func RunContext(ctx context.Context, s Service) {
	if ctx == nil {
		panic("nil context")
	}
	if s == nil {
		panic("nil service")
	}

	log := logger.Ctx(ctx)

	if err := runContext(ctx, s); err != nil && err != context.Canceled {
		log.Err(err).Msg("")
		os.Exit(1)
	}

	log.Debug().Msg("Normal exit")
}

func runContext(ctx context.Context, s Service) error {
	if stdlog.Flags() == stdlog.LstdFlags {
		stdlog.SetFlags(stdlog.Lshortfile)
	}

	log := logger.Ctx(ctx)

	// Connect to the message bus.
	conn, err := messaging.Dial(ctx)
	if err != nil {
		return err
	}
	defer logger.LoggedClose(log, conn, "message bus connection")

	ch, err := conn.Channel()
	if err != nil {
		return err
	}
	defer logger.LoggedClose(log, ch, "messaging channel")

	// Start the service's goroutines.
	if c, ok := s.(io.Closer); ok {
		defer logger.LoggedClose(log, c, "service", "stop")
	}

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	if err = s.Start(ctx, ch); err != nil {
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
