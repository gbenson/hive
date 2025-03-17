// Package service provides common code for Hive services.
package service

import (
	"context"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"os/signal"
	"syscall"

	"gbenson.net/hive/messaging"
)

type Service interface {
	// Start starts the service's goroutines.
	Start(ctx context.Context, ch *messaging.Channel) error
}

// Run a Hive service.
func Run(s Service) {
	if err := run(s); err != nil {
		fmt.Println("error:", err)
		os.Exit(1)
	}
}

func run(s Service) error {
	log.SetFlags(log.Lshortfile)

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
	if !noMonitor {
		defer rsm.Report(ch)
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

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	if err := s.Start(ctx, ch); err != nil {
		return err
	}

	// Send the restart monitor report.
	if !noMonitor {
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
			log.Printf("INFO: %s: shutting down", sig)
			cancel()
		}
	}
}
