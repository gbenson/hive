package wrappers

import (
	"iter"
	"time"

	. "gbenson.net/hive/logging/event"
)

// WrappedEvent is a base class with every [Event] and [Message]
// method defined as a pass through.
type WrappedEvent struct {
	Wrapped Event
}

// Wrap constructs a new WrappedEvent, avoiding the go vet "struct
// literal uses unkeyed fields" error that using `WrappedEvent{e}`
// will cause if you use that form outside of this package.
func Wrap(e Event) WrappedEvent {
	return WrappedEvent{e}
}

// Event methods.

func (e *WrappedEvent) Command() string {
	return e.Wrapped.Command()
}

func (e *WrappedEvent) ContainerName() string {
	return e.Wrapped.ContainerName()
}

func (e *WrappedEvent) Hostname() string {
	return e.Wrapped.Hostname()
}

func (e *WrappedEvent) ID() string {
	return e.Wrapped.ID()
}

func (e *WrappedEvent) Message() Message {
	return e.Wrapped.Message()
}

func (e *WrappedEvent) Priority() Priority {
	return e.Wrapped.Priority()
}

func (e *WrappedEvent) Time() time.Time {
	return e.Wrapped.Time()
}

// Message methods.  Having these means wrappers can be implemented in
// a single class, you don't need separate XEvent and XMessage classes
// for each.

func (e *WrappedEvent) Fields() map[string]any {
	return e.Wrapped.Message().Fields()
}

func (e *WrappedEvent) Pairs() iter.Seq2[string, any] {
	return e.Wrapped.Message().Pairs()
}

func (e *WrappedEvent) String() string {
	return e.Wrapped.Message().String()
}
