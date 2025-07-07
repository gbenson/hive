package downgrades

import (
	"testing"

	"gotest.tools/v3/assert"

	"gbenson.net/hive/logging"
	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/testevents"
)

func TestDowngradeNginxBufferWarning(t *testing.T) {
	const prefix = `2024/09/02 10:00:31 [warn] 39#39: *606 `
	const suffix = `, client: 64.225.101.100` +
		`, server: gbenson.net` +
		`, request: "GET /hello/world HTTP/1.1"` +
		`, host: "216.213.58.42"`

	for _, tc := range []struct {
		What, Where, Why string
	}{
		{"an upstream response", "fastcgi_temp/2/00", " while reading upstream"},
		{"a client request body", "client_temp", ""},
	} {
		msg := tc.What +
			` is buffered to a temporary file /var/cache/nginx/fastcgi_temp/` +
			tc.Where +
			`0000000001` +
			tc.Why

		me, err := NewTestNginxErrorEvent(prefix + msg + suffix)
		assert.NilError(t, err)

		e, err := logging.UnmarshalEvent(me)
		assert.NilError(t, err)
		assert.Equal(t, e.Message().Fields()["message"], msg)

		assert.Equal(t, e.Priority(), PriInfo)
	}
}

func TestNoDowngradeNginxBufferWarning(t *testing.T) {
	const prefix = `2024/09/02 10:00:31 [warn] 39#39: *606 `
	const suffix = `, client: 64.225.101.100` +
		`, server: gbenson.net` +
		`, request: "GET /hello/world HTTP/1.1"` +
		`, host: "216.213.58.42"`

	for _, tc := range []struct {
		What, Where, Why string
	}{
		{"an upstream response", "fastcgi_temp/2/00", ""},
		{"a client request body", "client_temp", " while reading upstream"},
	} {
		msg := tc.What +
			` is buffered to a temporary file /var/cache/nginx/fastcgi_temp/` +
			tc.Where +
			`0000000001` +
			tc.Why

		me, err := NewTestNginxErrorEvent(prefix + msg + suffix)
		assert.NilError(t, err)

		e, err := logging.UnmarshalEvent(me)
		assert.NilError(t, err)
		assert.Equal(t, e.Message().Fields()["message"], msg)

		assert.Equal(t, e.Priority(), PriWarning)
	}
}
