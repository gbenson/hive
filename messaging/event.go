package messaging

import (
	"strings"
	"time"

	cloudevents "github.com/cloudevents/sdk-go/v2"
	"github.com/gertd/go-pluralize"
	"github.com/google/uuid"

	"gbenson.net/hive/messaging/event"
	"gbenson.net/hive/util"
)

const (
	ApplicationCloudEventsJSON = cloudevents.ApplicationCloudEventsJSON
)

// Event is the canonical CloudEvent representation of an object.
type Event = event.Event

// CalculatedEventTypePrefix will be prefixed to CloudEvent "type"
// attributes calculated from the routing keys they were published to.
const CalculatedEventTypePrefix = "net.gbenson.hive."

// DefaultEventSource is the default value for the "source" attribute of
// CloudEvents created by this service.
var DefaultEventSource = "https://gbenson.net/hive/services/" + util.ServiceName()

// NewEvent returns a new [Event].
func NewEvent() *Event {
	e := cloudevents.NewEvent()
	return &e
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
