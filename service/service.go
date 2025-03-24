// Package service provides common code for Hive services.
package service

import (
	"context"
	"flag"
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
	Start(ctx context.Context, ch *messaging.Channel) error
}

// Run a Hive service.
func Run(s Service) {
	log := logger.New(&logger.Options{})
	RunContext(log.WithContext(context.Background()), s)
}

// Run a Hive service with the given context.
func RunContext(ctx context.Context, s Service) {
	if ctx == nil {
		panic("nil context")
	}

	if err := runContext(ctx, s); err != nil {
		logger.Ctx(ctx).Err(err).Msg("")
		os.Exit(1)
	}
}

func runContext(ctx context.Context, s Service) error {
	if s == nil {
		panic("nil service")
	}

	stdlog.SetFlags(stdlog.Lshortfile)

	var noMonitor bool
loop:
	for _, arg := range os.Args[1:] {
		switch arg {
		case "--no-monitor":
			fallthrough
		case "-no-monitor":
			noMonitor = true
			break loop
		}
	}

	// Run the restart monitor.
	rsm := RestartMonitor{}
	if !noMonitor {
		rsm.Run()
	}

	// Connect to the message bus.
	conn, err := messaging.Dial()
	if err != nil {
		return err
	}
	defer conn.Close()

	ch, err := conn.Channel()
	if err != nil {
		return err
	}
	defer ch.Close()

	reportSent := false
	if !noMonitor {
		defer func() {
			if !reportSent {
				rsm.Report(ch)
			}
		}()
	}

	// Set up -no-monitor in case s.Start() uses flag.
	flag.Bool(
		"no-monitor",
		false,
		"run without restart monitoring",
	)

	// Start the service's goroutines.
	if c, ok := s.(io.Closer); ok {
		defer c.Close()
	}

	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	if err := s.Start(ctx, ch); err != nil {
		return err
	}

	// Send the restart monitor report.
	if !noMonitor {
		reportSent = true
		rsm.Report(ch)
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
			logger.Ctx(ctx).Info().
				Str("reason", "signal").
				Str("signal", sig.String()).
				Msg("Shutting down")
			cancel()
		}
	}
}
