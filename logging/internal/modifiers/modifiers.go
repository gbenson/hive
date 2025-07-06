// Package modifiers provides the event modifier plugin system.
package modifiers

import (
	"maps"

	. "gbenson.net/hive/logging/event"
	"gbenson.net/hive/logging/internal/logger"
)

// An EventModifier returns a new modified event or returns the
// original event unmodified.
type EventModifier func(Event) Event

// eventModifiers are the registered event modifiers.
var eventModifiers = map[string]EventModifier{}

// Register registers an event modifier.
func Register(name string, f EventModifier) {
	eventModifiers[name] = f
}

// Apply applies all relevant modifiers.
func Apply(e Event) Event {
	modifiers := maps.Clone(eventModifiers)

loop:
	for len(modifiers) != 0 {
		for name, maybeWrap := range modifiers {
			if ee := maybeWrap(e); ee != e {
				e = ee
				logger.Logger.Trace().
					Str("event", e.ID()).
					Str("modifier", name).
					Msg("Event modified")

				delete(modifiers, name)
				continue loop
			}
		}
		break // nothing changed
	}

	return e
}
