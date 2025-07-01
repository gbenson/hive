// Package event provides the Event interface and supporting types.
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

	// Message returns the primary content of this logged event.
	Message() Message

	// Priority returns the RFC 5424 syslog severity level of this
	// event, as reported by the originating process.
	Priority() Priority

	// Time returns the wallclock time of the originating host when
	// the event was logged.
	Time() time.Time
}
