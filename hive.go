// Package hive provides common code for Hive services.
package hive

import (
	"context"
	"errors"
	"fmt"
	"io"
	stdlog "log"
	"os"
	"os/signal"
	"syscall"

	"golang.org/x/term"

	"gbenson.net/go/logger"
	"gbenson.net/hive/logging/event"
	"gbenson.net/hive/messaging"
	"gbenson.net/hive/util"
)

type MessagingService interface {
	// Start starts the service's goroutines.
	Start(ctx context.Context, ch messaging.Channel) (<-chan error, error)
}

type StandaloneService interface {
	// Start starts the service's goroutines.
	Start(ctx context.Context) (<-chan error, error)
}

// Run runs a Hive service.
func Run(s any) {
	log := logger.New(nil)
	if !term.IsTerminal(int(os.Stdout.Fd())) {
		log = log.With().
			Str(event.LoggerTagField, "hive-service-go").
			Logger()
	}
	RunContext(log.WithContext(context.Background()), s)
}

// RunContext runs a Hive service with the given context.
func RunContext(ctx context.Context, s any) {
	if ctx == nil {
		panic("nil context")
	}
	if s == nil {
		panic("nil service")
	}

	log := logger.Ctx(ctx).With().
		Str("service", "hive-"+util.ServiceName()).
		Logger()

	log.Info().Msg("Starting")

	if err := runContext(ctx, s); err != nil && err != context.Canceled {
		log.WithLevel(logger.LevelFor(err)).
			Err(err).
			Msg("Error exit")
		os.Exit(1)
	}

	log.Info().Msg("Normal exit")
}

func runContext(ctx context.Context, s any) error {
	if stdlog.Flags() == stdlog.LstdFlags {
		stdlog.SetFlags(stdlog.Lshortfile)
	}

	log := logger.Ctx(ctx)

	// Connect to the message bus if required.
	var ch messaging.Channel
	var closeC <-chan error
	if _, ok := s.(MessagingService); ok {
		conn, err := messaging.Dial(ctx)
		if err != nil {
			return err
		}
		defer logger.LoggedClose(log, conn, "message bus connection")
		closeC = conn.NotifyClose()

		ch, err = conn.Channel()
		if err != nil {
			return err
		}
		defer logger.LoggedClose(log, ch, "messaging channel")
	} else {
		closeC = make(chan error)
	}

	// Start the service's goroutines.
	if c, ok := s.(io.Closer); ok {
		defer logger.LoggedClose(log, c, "service", "stop")
	}

	ctx, stop := signal.NotifyContext(
		ctx,
		syscall.SIGHUP,
		syscall.SIGINT,
		syscall.SIGTERM,
	)
	defer stop()

	var errC <-chan error
	var err error
	switch ss := s.(type) {
	case MessagingService:
		errC, err = ss.Start(ctx, ch)
	case StandaloneService:
		errC, err = ss.Start(ctx)
	default:
		err = fmt.Errorf("service: unsupported type: %T", s)
	}
	if err != nil {
		return err
	}

	// Block until stopped or interrupted.
	//
	// Shutdown sequence:
	//   1. One of the following causes ctx to be canceled:
	//        - a service goroutine writes/closes errC
	//        - amqp client writes/closing closeC
	//        - one of the signals is recieved
	//   2. Canceling ctx resets the signal handlers, allowing the
	//      shutdown to be interrupted if it locks up or whatever.
	//   3. [If it wasn't a signal, select now reads context.Canceled]
	//   4. This function returns.
	//   5. [deferred service.Close is called, if installed]
	//   6. [deferred channel.Close is called]
	//   7. [deferred connection.Close is called. Thiswaits for the
	//      NotifyClose goroutine to exit, so if this wasn't the AMQP
	//      client closing the connection already then we will now
	//      wait for that to happen]
	//   8. Control finally returns to RunContext, which logs any error.

	for {
		select {
		case <-ctx.Done():
			if err == nil {
				// A signal was received.
				err = ctx.Err()
				if err == context.Canceled {
					err = nil
				}
			}
			return err

		case re, ok := <-closeC:
			err = channelShutdown(ctx, re, err, ok, "close notify")
			stop()

		case re, ok := <-errC:
			err = channelShutdown(ctx, re, err, ok, "service error")
			stop()
		}
	}
}

var closedChannels = make(map[string]bool)

func channelShutdown(
	ctx context.Context,
	thisEvent, shutdownCause error,
	isChannelOpen bool,
	channelName string,
) error {
	log := logger.Ctx(ctx).With().Str("channel", channelName).Logger()

	if thisEvent == nil {
		if isChannelOpen {
			thisEvent = errors.New("nil error")
		} else {
			thisEvent = channelClosed(channelName)
		}
	}

	if shutdownCause != nil {
		log.Debug().
			Err(thisEvent).
			Str("when", "during shutdown").
			Msg("Activity")

		return shutdownCause
	}

	log.Err(thisEvent).Msg("Initiating shutdown")

	return thisEvent
}

func channelClosed(name string) error {
	err := fmt.Errorf("%s channel: closed", name)
	if closedChannels[name] {
		err = fmt.Errorf("%w again!", err)
	} else {
		closedChannels[name] = true
	}
	return err
}
