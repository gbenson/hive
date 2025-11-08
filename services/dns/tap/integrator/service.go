package integrator

import (
	"context"
	"encoding/json"
	"maps"
	"slices"
	"sync"
	"time"

	"github.com/miekg/dns"

	"gbenson.net/go/logger"
	"gbenson.net/hive/config"
	"gbenson.net/hive/messaging"
)

const (
	ConfigKeyPrefix = "query_integrator"

	DefaultWindow = 2 * time.Second
	DefaultTick   = 100 * time.Millisecond
)

type Service struct {
	mu   sync.Mutex
	pubC chan *queryEvent

	// Debugging.
	LogEvents bool

	// Multi-server event correlation.
	InternalServerID string
	InternalServerIP string
	parkedIFQs       parkedEventMap
	parkedOCQs       parkedEventMap
	Window           time.Duration
	Tick             time.Duration
}

// init configures the service.
func (s *Service) init(ctx context.Context) error {
	c := config.New("dnstap")
	if err := c.Read(); err != nil {
		return err
	}

	if !s.LogEvents {
		ck := ConfigKeyPrefix + ".log.events"
		s.LogEvents = c.GetBool(ck)
	}

	if s.InternalServerID == "" {
		ck := ConfigKeyPrefix + ".internal_server.name"
		s.InternalServerID = c.GetString(ck)
		if s.InternalServerID == "" {
			return ConfigError(ck)
		}
	}

	if s.InternalServerIP == "" {
		ck := ConfigKeyPrefix + ".internal_server.addr"
		s.InternalServerIP = c.GetString(ck)
		if s.InternalServerIP == "" {
			return ConfigError(ck)
		}
	}

	if s.Window == 0 {
		ck := ConfigKeyPrefix + ".window"
		c.SetDefault(ck, DefaultWindow)
		s.Window = c.GetDuration(ck)
	}

	if s.Tick == 0 {
		ck := ConfigKeyPrefix + ".tick"
		c.SetDefault(ck, DefaultTick)
		s.Tick = c.GetDuration(ck)
	}

	logger.Ctx(ctx).Info().
		Str("internal_server_id", s.InternalServerID).
		Str("internal_server_addr", s.InternalServerIP).
		Str("window", s.Window.String()).
		Str("tick", s.Tick.String()).
		Msg("Configured")

	return nil
}

// Start starts the service's goroutines.
func (s *Service) Start(
	ctx context.Context,
	ch messaging.Channel,
) (<-chan error, error) {
	if err := s.init(ctx); err != nil {
		return nil, err
	}

	// Start the publisher goroutine.
	errC := make(chan error, 2)
	s.pubC = make(chan *queryEvent, 1000)

	go func() {
		var err error
		for err == nil {
			select {
			case <-ctx.Done():
				err = ctx.Err()

			case q := <-s.pubC:
				err = s.augmentAndRepublishNow(ctx, q)
			}
		}
		errC <- err
	}()

	// Start the processor goroutine.
	s.parkedIFQs = make(parkedEventMap)
	s.parkedOCQs = make(parkedEventMap)

	ticker := time.NewTicker(s.Tick)

	go func() {
		var err error
		for err == nil {
			select {
			case <-ctx.Done():
				err = ctx.Err()

			case <-ticker.C:
				err = s.processParkedEvents(ctx)
			}
		}
		errC <- err
	}()

	// Start the consumer goroutine.
	return errC, ch.ConsumeExclusive(ctx, "dnstap.events", s)
}

// Consume consumes one dnstap event.
func (s *Service) Consume(
	ctx context.Context,
	ch messaging.Channel,
	me *messaging.Event,
) error {
	if s.LogEvents {
		if b, err := json.Marshal(me); err == nil {
			logger.Ctx(ctx).Debug().RawJSON("event", b).Msg("Received")
		}
	}

	var dt dnstap
	if err := me.DataAs(&dt); err != nil {
		return err
	} else if dt.Type != "MESSAGE" {
		return nil
	}

	switch dt.Message.Type {
	case "CLIENT_QUERY", "FORWARDER_QUERY":
		return s.consumeQuery(ctx, ch, me, &dt)
	}

	return nil
}

// consumeQuery consumes one dnstap query event.
func (s *Service) consumeQuery(
	ctx context.Context,
	ch messaging.Channel,
	me *messaging.Event,
	dt *dnstap,
) error {
	var qm dns.Msg
	if err := qm.Unpack(dt.Message.QueryMessage); err != nil {
		return err
	}

	// From https://pkg.go.dev/github.com/miekg/dns#Question:
	// While the original DNS RFCs allow multiple questions per
	// message, in practice most DNS servers consider multiple
	// questions to be an error and it's recommended to only have
	// one question per message.
	switch len(qm.Question) {
	case 0:
		return ErrNoQuestions
	default:
		return ErrTooManyQuestions
	case 1:
	}

	qq := Question(qm.Question[0])
	q := &queryEvent{ch, me, dt, &qq}

	if q.dt.Identity == s.InternalServerID {
		return s.handleInnerQuery(ctx, q)
	} else {
		return s.handleOuterQuery(ctx, q)
	}
}

// A queryEvent is an in-flight dnstap query event.
type queryEvent struct {
	ch       messaging.Channel
	me       *messaging.Event
	dt       *dnstap
	question *Question
}

// handleInnerQuery handles dnstap query events from servers
// on the inner network.
func (s *Service) handleInnerQuery(ctx context.Context, q *queryEvent) (err error) {
	switch q.dt.Message.Type {
	case "CLIENT_QUERY":
		err = s.augmentAndRepublish(ctx, q)
	case "FORWARDER_QUERY":
		s.parkInnerForwarderQuery(s.newParkedEvent(q))
	}

	return
}

// handleOuterQuery handles dnstap query events from servers
// on the outer network.
func (s *Service) handleOuterQuery(ctx context.Context, q *queryEvent) (err error) {
	switch {
	case q.dt.Message.Type != "CLIENT_QUERY":
		// do nothing
	case q.dt.Message.QueryIP != s.InternalServerIP:
		err = s.augmentAndRepublish(ctx, q)
	default:
		s.parkOuterClientQuery(s.newParkedEvent(q))
	}

	return
}

// A parkedEvent is a queryEvent being held for correlation.
type parkedEvent struct {
	q        *queryEvent
	deadline time.Time
}

// A parkedEventMap hashes parkedEvents by stringified question.
type parkedEventMap map[string][]*parkedEvent

func (s *Service) newParkedEvent(q *queryEvent) *parkedEvent {
	return &parkedEvent{q, time.Now().Add(s.Window)}
}

// parkInnerForwarderQuery parks a FORWARDER_QUERY dnstap event
// from an internal server.
func (s *Service) parkInnerForwarderQuery(e *parkedEvent) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	k := e.q.question.String()
	s.parkedIFQs[k] = append(s.parkedIFQs[k], e)
	return nil
}

// parkOuterClientQuery parks a CLIENT_QUERY dnstap event from
// a server in the DMZ.
func (s *Service) parkOuterClientQuery(e *parkedEvent) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	k := e.q.question.String()
	s.parkedOCQs[k] = append(s.parkedOCQs[k], e)
	return nil
}

// processParkedEvents runs every tick.
func (s *Service) processParkedEvents(ctx context.Context) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if err := s.parkedOCQs.releaseExpired(ctx, s); err != nil {
		return err
	}

	s.parkedIFQs.deleteExpired()
	s.parkedIFQs.deleteCorrelated(s.parkedOCQs)

	return nil
}

func (m parkedEventMap) releaseExpired(ctx context.Context, s *Service) error {
	now := time.Now()

	for _, k := range slices.Collect(maps.Keys(m)) {
		u := m[k]
		var v []*parkedEvent

		for _, e := range u {
			if !now.After(e.deadline) {
				v = append(v, e)
				continue
			}
			if err := s.augmentAndRepublish(ctx, e.q); err != nil {
				return err
			}
		}
		m.maybeReplace(k, u, v)
	}

	return nil
}

func (m parkedEventMap) deleteExpired() {
	now := time.Now()

	for _, k := range slices.Collect(maps.Keys(m)) {
		u := m[k]
		v := slices.DeleteFunc(u, func(e *parkedEvent) bool {
			return now.After(e.deadline)
		})
		m.maybeReplace(k, u, v)
	}
}

func (m parkedEventMap) deleteCorrelated(n parkedEventMap) {
	if len(m) == 0 || len(n) == 0 {
		return
	}

	for _, k := range slices.Collect(maps.Keys(m)) {
		un := n[k]
		if len(un) == 0 {
			continue
		}
		um := m[k]

		vm, vn := deleteCorrelated(um, un)

		m.maybeReplace(k, um, vm)
		n.maybeReplace(k, un, vn)
	}
}

func (m parkedEventMap) maybeReplace(k string, u, v []*parkedEvent) {
	switch len(v) {
	case 0:
		delete(m, k)
	case len(u):
		// no change
	default:
		m[k] = v
	}
}

func deleteCorrelated(a, b []*parkedEvent) ([]*parkedEvent, []*parkedEvent) {
	for {
		ia, ib, found := bestCorrelation(a, b)
		if !found {
			return a, b
		}

		a = slices.Delete(a, ia, ia+1)
		b = slices.Delete(b, ib, ib+1)
	}
}

func bestCorrelation(a, b []*parkedEvent) (bestIA, bestIB int, found bool) {
	bestDelta := 500 * time.Millisecond
	for ia, ea := range a {
		ta := ea.q.dt.Message.QueryTime
		for ib, eb := range b {
			tb := eb.q.dt.Message.QueryTime

			delta := tb.Sub(ta)
			if delta < 0 {
				delta = -delta
			}
			if bestDelta < delta {
				continue
			}
			bestIA = ia
			bestIB = ib
			found = true
		}
	}

	return
}

// augmentAndRepublish schedules the given queryEvent to be augmented
// and republished.
func (s *Service) augmentAndRepublish(ctx context.Context, q *queryEvent) error {
	select {
	case s.pubC <- q:
		return nil
	default:
		return ErrPublishBufferFull
	}
}

// augmentAndRepublishNow augments and republishes the given queryEvent.
// Don't call this directly, use augmentAndRepublish instead.
func (s *Service) augmentAndRepublishNow(ctx context.Context, q *queryEvent) error {
	var payload map[string]any
	if err := q.me.DataAs(&payload); err != nil {
		return err
	}

	// Augment.
	msg, ok := payload["message"].(map[string]any)
	if !ok || msg["query_question"] != nil {
		b, err := json.Marshal(q.me)
		if err != nil {
			return err
		}

		logger.Ctx(ctx).Error().
			RawJSON("event", b).
			Msg("Unable to republish")

		return nil
	}
	msg["query_question"] = q.question

	// Republish.
	event := messaging.NewEvent()
	event.SetID(q.me.ID())
	//event.SetTime(dt.QueryTime())
	event.SetData("application/json", payload)

	if err := q.ch.PublishEvent(ctx, "dnstap.query.events", event); err != nil {
		return err
	}

	if s.LogEvents {
		if b, err := json.Marshal(event); err == nil {
			logger.Ctx(ctx).Debug().RawJSON("event", b).Msg("Published")
		}
	}

	return nil
}
