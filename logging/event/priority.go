package event

// Priority is the RFC 5424 syslog severity level of an event. See
// https://wiki.archlinux.org/title/Systemd/Journal#Priority_level
// for details.
type Priority int

const (
	PriEmerg Priority = iota
	PriAlert
	PriCrit
	PriErr
	PriWarning
	PriNotice
	PriInfo
	PriDebug

	// Priority to assign to events with missing/invalid priority
	// values.  PriNotice ("Events that are unusual, but not error
	// conditions") seems about right.
	PriUnknown = PriNotice
)
