package monitor

import (
	"context"
	"fmt"
	"strings"
	"time"

	"gbenson.net/go/logger"
	"gbenson.net/hive/apps/console" // XXX factor out
	"gbenson.net/hive/messaging"
)

type Service struct {
}

// Start starts the service's goroutines.
func (s *Service) Start(
	ctx context.Context,
	ch messaging.Channel,
) (<-chan error, error) {
	return nil, ch.ConsumeExclusive(ctx, "dnstap.query.events", s)
}

// Consume consumes one event.
func (s *Service) Consume(
	ctx context.Context,
	ch messaging.Channel,
	me *messaging.Event,
) error {
	log := logger.Ctx(ctx).
		With().
		Interface("event", me).
		Logger()

	log.Debug().Msg("Received")

	var dt dnstap
	if err := me.DataAs(&dt); err != nil {
		log.Err(err).Msg("")
		return nil
	}

	fmt.Println(dt.Event.String())
	return nil
}

// Partially decoded "net.gbenson.hive.dnstap_query_event" CloudEvent payload.
type dnstap struct {
	Event Query `json:"message"`
}

type Query struct {
	Time      time.Time `json:"query_time"`     // from coredns
	OriginIP  string    `json:"query_address"`  // from coredns
	OriginMAC string    `json:"query_hwaddr"`   // added by hive-dns-collector
	Question  Question  `json:"query_question"` // added by hive-dns-integrator
}

type Question struct {
	Name  string `json:"name"`  // example.com.
	Class string `json:"class"` // IN
	Type  string `json:"type"`  // A
}

func (q *Query) String() string {
	var b console.Builder

	b.WriteTime(q.Time)

	b.WriteSpace()
	b.WriteString(Purple2(q.OriginIP))

	if hw := q.OriginMAC; hw != "" {
		b.WriteSpace()
		b.WriteString(Purple1(hw))
	}

	b.WriteSpace()
	b.WriteString(q.Question.String())

	return b.String()
}

func (q *Question) String() string {
	a, dot := strings.CutSuffix(q.Name, ".")
	b := q.Class + " " + q.Type

	if dot {
		b = ". " + b
	} else {
		a += " "
	}

	return a + MidGrey(b)
}

func Purple1(s string) string {
	return fmt.Sprintf("%s38;5;105m%s%s", console.CSI, s, console.RESET)
}

func Purple2(s string) string {
	return fmt.Sprintf("%s38;5;141m%s%s", console.CSI, s, console.RESET)
}

var MidGrey = console.MidGrey
