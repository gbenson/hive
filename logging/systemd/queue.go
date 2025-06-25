package systemd

const (
	// EventsQueue is where log collectors publish systemd journal
	// entries they collect.
	EventsQueue = "systemd.journal.events"

	// EventType is the CloudEvent type of systemd journal entries
	// published to EventsQueue.
	EventType = "net.gbenson.hive.systemd_journal_event"
)
