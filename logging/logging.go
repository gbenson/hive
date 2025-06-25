// Package logging provides centralized logging services for Hive.
package logging

import "gbenson.net/hive/logging/systemd"

// RawEventsQueue is where hive-log-collector publishes the events it collects.
const RawEventsQueue = systemd.EventsQueue

// Event represents a single logged event.
type Event = systemd.JournalEntry
