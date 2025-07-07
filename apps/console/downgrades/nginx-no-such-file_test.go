package downgrades

import (
	"testing"

	"gotest.tools/v3/assert"

	"gbenson.net/hive/logging"
	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/testevents"
)

func TestDowngradeNginxNoSuchFileError(t *testing.T) {
	const prefix = `2024/09/02 10:00:31 [error] 39#39: *606 `
	const suffix = ` (2: No such file or directory)` +
		`, client: 64.225.101.100` +
		`, server: gbenson.net` +
		`, request: "GET /hello/world HTTP/1.1"` +
		`, host: "216.213.58.42"` +
		`, referrer: "http://216.213.58.42:80/v2/"`

	for _, msg := range []string{
		`"/usr/share/nginx/html/hello/world" is not found`,
		`open() "/usr/share/nginx/html/hello/world" failed`,
	} {
		me, err := NewTestNginxErrorEvent(prefix + msg + suffix)
		assert.NilError(t, err)

		e, err := logging.UnmarshalEvent(me)
		assert.NilError(t, err)

		assert.Equal(t, e.Priority(), PriInfo)
	}
}

func TestNoDowngradeNginxNoSuchFileError(t *testing.T) {
	const suffix = ` (2: No such file or directory)` +
		`, client: 64.225.101.100` +
		`, server: gbenson.net` +
		`, request: "GET /hello/world HTTP/1.1"` +
		`, host: "216.213.58.42"` +
		`, referrer: "http://216.213.58.42:80/v2/"`

	for _, tc := range []struct {
		Level, Message string
	}{
		{"warn", `"/usr/share/nginx/html/hello/world" is not found`},
		{"error", `"/usr/share/nginx/html/../hello/world" is not found`},
		{"error", `"/usr/share/nginx/hello/world" is not found`},
		{"error", `open() "/usr/share/nginx/html/hello/world" is not found`},
		{"error", `"/usr/share/nginx/html/hello/world" failed`},
	} {
		prefix := `2024/09/02 10:00:31 [` + tc.Level + `] 39#39: *606 `
		me, err := NewTestNginxErrorEvent(prefix + tc.Message + suffix)
		assert.NilError(t, err)

		e, err := logging.UnmarshalEvent(me)
		assert.NilError(t, err)

		var wantPriority Priority
		switch tc.Level {
		case "warn":
			wantPriority = PriWarning
		case "error":
			wantPriority = PriErr
		default:
			t.Fatalf("%v: unhandled", tc.Level)
		}
		assert.Equal(t, e.Priority(), wantPriority)
	}
}
