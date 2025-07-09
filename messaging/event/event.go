// Package event provides the [Event] type.
package event

import (
	"reflect"

	"github.com/cloudevents/sdk-go/v2/event"
)

// Event is the canonical CloudEvent representation of an object.
type Event = event.Event

// New returns a new [Event].
func New() *Event {
	e := event.New()
	return &e
}

// UnmarshalJSON unmarshals a CloudEvent from its JSON-encoded form.
func UnmarshalJSON(b []byte) (*Event, error) {
	e := New()
	if err := e.UnmarshalJSON(b); err != nil {
		return nil, err
	}
	return e, nil
}

// Marshal returns the CloudEvent representation of v.
func Marshal(v any) (*Event, error) {
	if e, ok := v.(*Event); ok {
		return e, nil
	}

	if em, ok := v.(Marshaler); ok {
		return em.MarshalEvent()
	}

	return nil, &UnsupportedTypeError{reflect.TypeOf(v)}
}

// Marshaler is the interface implemented by types that can
// marshal themselves into CloudEvents.
type Marshaler interface {
	MarshalEvent() (*Event, error)
}

// Unmarshal unmarshals the CloudEvent representation of v.
func Unmarshal(e *Event, v any) error {
	if um, ok := v.(Unmarshaler); ok {
		return um.UnmarshalEvent(e)
	}

	return &UnsupportedTypeError{reflect.TypeOf(v)}
}

// Unmarshaler is the interface implemented by types that can
// unmarshal CloudEvent representations of themselves.
type Unmarshaler interface {
	UnmarshalEvent(*Event) error
}
