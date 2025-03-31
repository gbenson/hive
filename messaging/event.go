package messaging

import (
	"reflect"

	cloudevents "github.com/cloudevents/sdk-go/v2"

	"gbenson.net/hive/util"
)

const (
	ApplicationCloudEventsJSON = cloudevents.ApplicationCloudEventsJSON
)

type Event = cloudevents.Event

// DefaultSource is the default value for the "source" attribute of
// CloudEvents created by this service.
var DefaultSource = "https://gbenson.net/hive/services/" + util.ServiceName()

func NewEvent() *Event {
	e := cloudevents.NewEvent()
	e.SetSource(DefaultSource)
	return &e
}

// Marshal returns v as an [Event].
func MarshalEvent(v any) (*Event, error) {
	if e, ok := v.(*Event); ok {
		return e, nil
	}

	if em, ok := v.(EventMarshaler); ok {
		return em.MarshalEvent()
	}

	return nil, &UnsupportedTypeError{reflect.TypeOf(v)}
}

// EventMarshaler is the interface implemented by types that can
// marshal themselves into [Event]s.
type EventMarshaler interface {
	MarshalEvent() (*Event, error)
}

// An UnsupportedTypeError is returned by [MarshalEvent] when
// attempting to encode an unsupported value type.
type UnsupportedTypeError struct {
	Type reflect.Type
}

func (e *UnsupportedTypeError) Error() string {
	return "MarshalEvent: unsupported type: " + e.Type.String()
}
