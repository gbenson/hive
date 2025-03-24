package messaging

import (
	cloudevents "github.com/cloudevents/sdk-go/v2"

	"gbenson.net/hive/util"
)

const (
	ApplicationCloudEventsJSON = cloudevents.ApplicationCloudEventsJSON
	ApplicationJSON            = cloudevents.ApplicationJSON
)

type Event = cloudevents.Event

// DefaultSource is the default value for the "source" attribute of
// CloudEvents created by this service.
var DefaultSource = "https://gbenson.net/hive/services/" + util.ServiceName()

func NewEvent() Event {
	e := cloudevents.NewEvent()
	e.SetSource(DefaultSource)
	return e
}
