package mongo

// Filters are a last-resort to handle message spam that cannot
// otherwise be configured out.  Strive to avoid adding more!

import (
	"encoding/json"
	"strings"
)

type baseEvent struct {
	Severity  string `json:"s"`
	Component string `json:"c"`
	Context   string `json:"ctx"`
	Message   string `json:"msg"`
}

type wtCheckpointerMessage struct {
	Session   string `json:"session_name"`
	Category  string `json:"category"`
	Verbosity string `json:"verbose_level"`
	Message   string `json:"msg"`
}

type wtCheckpointerAttrs struct {
	Message wtCheckpointerMessage `json:"message"`
}

type wtCheckpointerEvent struct {
	baseEvent
	Attrs wtCheckpointerAttrs `json:"attr"`
}

func IsMongoNoise(event map[string]string) bool {
	const WantSeverity = "I" // informational
	const WantComponent = "WTCHKPT"
	const WantMessage = "WiredTiger message"
	const WantCategory = "WT_VERB_CHECKPOINT_PROGRESS"
	const WantVerbosity = "DEBUG_1"
	const WantPrefix = "saving checkpoint snapshot min: "

	// Quickly reject non-matching events.
	s := event["MESSAGE"]
	if !strings.Contains(s, WantCategory) {
		return false
	}

	// Carefully examine potential matches.
	var e wtCheckpointerEvent
	if err := json.Unmarshal([]byte(s), &e); err != nil {
		return false
	}
	m := e.Attrs.Message

	return e.Severity == WantSeverity &&
		e.Component == WantComponent &&
		e.Message == WantMessage &&
		m.Category == WantCategory &&
		m.Verbosity == WantVerbosity &&
		strings.HasPrefix(m.Message, WantPrefix)
}
