package logging

import (
	"iter"
	"time"
)

// wrappedEvent is a base class with every [Event] and [Message]
// method defined as a pass through.
type wrappedEvent struct {
	w Event
}

// Event methods.

func (e *wrappedEvent) Command() string {
	return e.w.Command()
}

func (e *wrappedEvent) ContainerName() string {
	return e.w.ContainerName()
}

func (e *wrappedEvent) Hostname() string {
	return e.w.Hostname()
}

func (e *wrappedEvent) Message() Message {
	return e.w.Message()
}

func (e *wrappedEvent) Priority() Priority {
	return e.w.Priority()
}

func (e *wrappedEvent) Time() time.Time {
	return e.w.Time()
}

// Message methods.  Having these means wrappers can be implemented in
// a single class, you don't need separate XEvent and XMessage classes
// for each.

func (e *wrappedEvent) Fields() map[string]any {
	return e.w.Message().Fields()
}

func (e *wrappedEvent) Pairs() iter.Seq2[string, any] {
	return e.w.Message().Pairs()
}

func (e *wrappedEvent) String() string {
	return e.w.Message().String()
}
