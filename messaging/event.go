package messaging

import (
	"bytes"
	"reflect"
	"strings"
	"time"

	cloudevents "github.com/cloudevents/sdk-go/v2"
	"github.com/cloudevents/sdk-go/v2/event"
	"github.com/gertd/go-pluralize"
	"github.com/google/uuid"

	"gbenson.net/hive/util"
)

const (
	ApplicationCloudEventsJSON = cloudevents.ApplicationCloudEventsJSON
)

type Event = cloudevents.Event

// CalculatedEventTypePrefix will be prefixed to CloudEvent "type"
// attributes calculated from the routing keys they were published to.
const CalculatedEventTypePrefix = "net.gbenson.hive."

// DefaultEventSource is the default value for the "source" attribute of
// CloudEvents created by this service.
var DefaultEventSource = "https://gbenson.net/hive/services/" + util.ServiceName()

func NewEvent() *Event {
	e := cloudevents.NewEvent()
	return &e
}

// NewEventFromJSON parses the JSON-encoded data into an [Event].
func NewEventFromJSON(b []byte) (*Event, error) {
	e := NewEvent()
	if err := UnmarshalJSONEvent(e, b); err != nil {
		return nil, err
	}
	return e, nil
}

// UnmarshalJSONEvent parses the JSON-encoded data and stores the
// result in the value pointed to by e.
func UnmarshalJSONEvent(e *Event, b []byte) error {
	return event.ReadJson(e, bytes.NewReader(b))
}

// MarshalEvent returns v as an [Event].
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

// UnmarshalEvent unmarshals an [Event] into v.
func UnmarshalEvent(e *Event, v any) error {
	if um, ok := v.(EventUnmarshaler); ok {
		return um.UnmarshalEvent(e)
	}

	return &UnsupportedTypeError{reflect.TypeOf(v)}
}

type EventUnmarshaler interface {
	UnmarshalEvent(*Event) error
}

// An UnsupportedTypeError is returned by [MarshalEvent] when
// attempting to encode an unsupported value type.
type UnsupportedTypeError struct {
	Type reflect.Type
}

func (e *UnsupportedTypeError) Error() string {
	return "event: unsupported type: " + e.Type.String()
}

// completeEvent supplies default values for the "id", "source",
// "type" and "time" attributes, if unset.
func completeEvent(e *Event, routingKey string) error {
	if e.ID() == "" {
		eventID, err := uuid.NewRandom()
		if err != nil {
			return err
		}
		e.SetID(eventID.String())
	}

	if e.Source() == "" {
		e.SetSource(DefaultEventSource)
	}

	if e.Type() == "" {
		e.SetType(eventTypeFromRoutingKey(routingKey))
	}

	if e.Time().IsZero() {
		e.SetTime(time.Now().UTC())
	}

	return nil
}

var pluralizer *pluralize.Client

// eventTypeFromRoutingKey calculates a default value for the "type"
// attribute, based on the routing key it's being published to.
func eventTypeFromRoutingKey(routingKey string) string {
	if pluralizer == nil {
		pluralizer = pluralize.NewClient()
	}

	parts := strings.Split(routingKey, ".")
	pi := len(parts) - 1
	parts[pi] = pluralizer.Singular(parts[pi])

	return CalculatedEventTypePrefix + strings.Join(parts, "_")
}
