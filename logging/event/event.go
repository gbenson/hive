// Package event provides the Event interface.
package event

import "time"

// Event represents a single logged event.
type Event interface {
	// Command returns the name of the originating process.  Generally
	// this will be the name you would see in top, so mostly lowercase
	// alphanumerics with hyphens or underscores, but be prepared for
	// the occasional random one with brackets or parentheses.
	Command() string

	// ContainerName returns the name of the container the originating
	// process is running in.  Will be empty if the originating
	// process isn't in a container, or if the originating process is
	// in a container managed by an engine we don't yet handle.
	ContainerName() string

	// Hostname returns the name of the originating host.
	Hostname() string

	// Message returns the human-readable text of this logged event,
	// as supplied by the originating process.  This is the primary
	// text intended to be shown to the user.  Note that newline
	// characters are permitted.
	Message() string

	// Time returns the wallclock time of the originating host when the
	// event was logged.
	Time() time.Time
}
