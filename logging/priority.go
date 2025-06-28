package logging

import "gbenson.net/hive/logging/event"

// Priority is the RFC 5424 syslog severity level of an event.
type Priority = event.Priority

const (
	PriEmerg   = event.PriEmerg
	PriAlert   = event.PriAlert
	PriCrit    = event.PriCrit
	PriErr     = event.PriErr
	PriWarning = event.PriWarning
	PriNotice  = event.PriNotice
	PriInfo    = event.PriInfo
	PriDebug   = event.PriDebug
	PriUnknown = event.PriUnknown
)

type priorityMap map[any]Priority

func (m priorityMap) Get(v any) Priority {
	if p, ok := m[v]; ok {
		return p
	}
	return PriUnknown
}
