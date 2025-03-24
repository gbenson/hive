// Package logger provides logging for Hive libraries and services.
package logger

import (
	"context"
	"io"
	"os"

	"github.com/rs/zerolog"
)

var DefaultLevel = zerolog.LevelInfoValue

type Logger = zerolog.Logger

type Options struct {
	Writer io.Writer
	Level  string
}

// New creates a new logger.
func New(options *Options) Logger {
	if options == nil {
		panic("nil options")
	}

	writer := options.Writer
	if writer == nil {
		writer = zerolog.NewConsoleWriter()
	}
	log := zerolog.New(writer)

	level, err := zerolog.ParseLevel(options.level())
	if err != nil {
		log.Warn().Err(err).Msg("")
	}
	if level != zerolog.NoLevel {
		log = log.Level(level)
	}

	return log
}

func (o *Options) level() string {
	if s := o.Level; s != "" {
		return s
	}
	if s := os.Getenv("LOG_LEVEL"); s != "" {
		return s
	}
	if s := os.Getenv("LL"); s != "" {
		return s
	}
	return DefaultLevel
}

// Ctx returns the Logger associated with the given context. Returns
// an appropriate (non-nil) default if ctx has no associated logger.
func Ctx(ctx context.Context) *Logger {
	if ctx == nil {
		panic("nil context")
	}

	return zerolog.Ctx(ctx)
}
