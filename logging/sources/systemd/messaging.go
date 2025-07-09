package systemd

import (
	"time"

	messaging_event "gbenson.net/hive/messaging/event"
)

// EventsQueue is where log collectors publish system journal entries
// they collect.
const EventsQueue = "systemd.journal.events"

// EventType is the CloudEvent type of systemd journal entries
// published to EventsQueue.
const EventType = "net.gbenson.hive.systemd_journal_event"

// MarshalEvent implements the [messaging_event.Marshaler] interface.
func (entry *JournalEntry) MarshalEvent() (*messaging_event.Event, error) {
	event := messaging_event.New()

	// Hoist the digest into the envelope.
	digest := entry.Blake2b256Digest()
	switch entry.Digest {
	case digest:
		entry = clone(entry)
		entry.Digest = ""
		fallthrough
	case "":
		event.SetID(digest)
	default:
		return nil, &DigestError{Got: entry.Digest, Want: digest}
	}

	// Hoist the collection timestamp into the envelope.
	if entry.CollectionTimestamp != 0 {
		event.SetTime(time.Unix(0, entry.CollectionTimestamp))
		entry = clone(entry)
		entry.CollectionTimestamp = 0
	}

	event.SetData("application/json", entry)

	return event, nil
}

// UnmarshalEvent unmarshals a [messaging_event.Event] into a [JournalEntry].
func UnmarshalEvent(event *messaging_event.Event) (*JournalEntry, error) {
	var entry JournalEntry
	if err := messaging_event.Unmarshal(event, &entry); err != nil {
		return nil, err
	}
	return &entry, nil
}

// UnmarshalEvent implements the [messaging_event.Unarshaler] interface.
func (entry *JournalEntry) UnmarshalEvent(event *messaging_event.Event) error {
	if err := event.DataAs(entry); err != nil {
		return err
	}

	// Sink the collection timestamp and digest, if necessary.
	if entry.CollectionTimestamp == 0 {
		entry.CollectionTimestamp = event.Time().UnixNano()
	}
	if entry.Digest == "" {
		entry.Digest = event.ID()
	}

	return nil
}
