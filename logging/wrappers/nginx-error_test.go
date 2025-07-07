package wrappers

import (
	"testing"

	"gotest.tools/v3/assert"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/testevents"
)

func TestBasicNotice(t *testing.T) {
	const in = `2024/09/02 10:00:31 [notice] 1#1: hello world`

	me, err := NewTestNginxErrorEvent(in)
	assert.NilError(t, err)

	e, err := unmarshalEvent(me)
	assert.NilError(t, err)
	assert.Equal(t, e.Message().String(), in)

	_, ok := e.(*NginxErrorEvent)
	assert.Assert(t, ok, e.Message())

	assert.DeepEqual(t, e.Message().Fields(), map[string]any{
		"level":   "notice",
		"message": "hello world",
		"pid":     "1",
		"tid":     "1",
		"time":    "2024/09/02 10:00:31",
	})

	assert.Equal(t, e.Priority(), PriNotice)
}

func TestBasicWarning(t *testing.T) {
	const msg = `a client request body is buffered to a temporary ` +
		`file /var/cache/nginx/client_temp/0000000001`
	const extra = `, client: 216.213.58.42, server: gbenson.net, ` +
		`request: "POST /w/api.php HTTP/2.0", host: "gbenson.net"`
	const in = `2024/09/02 10:00:31 [warn] 39#39: *606 ` + msg + extra

	me, err := NewTestNginxErrorEvent(in)
	assert.NilError(t, err)

	e, err := unmarshalEvent(me)
	assert.NilError(t, err)
	assert.Equal(t, e.Message().String(), in)

	_, ok := e.(*NginxErrorEvent)
	assert.Assert(t, ok, e.Message())

	assert.DeepEqual(t, e.Message().Fields(), map[string]any{
		"client":  "216.213.58.42",
		"conn":    "606",
		"host":    "gbenson.net",
		"level":   "warn",
		"message": msg,
		"pid":     "39",
		"request": "POST /w/api.php HTTP/2.0",
		"server":  "gbenson.net",
		"tid":     "39",
		"time":    "2024/09/02 10:00:31",
	})

	assert.Equal(t, e.Priority(), PriWarning)
}

func TestBasicError(t *testing.T) {
	const msg = `"/usr/share/nginx/html/hello/world" is not found ` +
		`(2: No such file or directory)`
	const extra = `, client: 64.225.101.100, server: gbenson.net, ` +
		`request: "GET /hello/world HTTP/1.1", host: "216.213.58.42", ` +
		`referrer: "http://216.213.58.42:80/v2/"`
	const in = `2024/09/02 10:00:31 [error] 39#39: *606 ` + msg + extra

	me, err := NewTestNginxErrorEvent(in)
	assert.NilError(t, err)

	e, err := unmarshalEvent(me)
	assert.NilError(t, err)
	assert.Equal(t, e.Message().String(), in)

	_, ok := e.(*NginxErrorEvent)
	assert.Assert(t, ok, e.Message())

	assert.DeepEqual(t, e.Message().Fields(), map[string]any{
		"client":   "64.225.101.100",
		"conn":     "606",
		"host":     "216.213.58.42",
		"level":    "error",
		"message":  msg,
		"pid":      "39",
		"referrer": "http://216.213.58.42:80/v2/",
		"request":  "GET /hello/world HTTP/1.1",
		"server":   "gbenson.net",
		"tid":      "39",
		"time":     "2024/09/02 10:00:31",
	})

	assert.Equal(t, e.Priority(), PriErr)
}

func TestMessyError(t *testing.T) {
	const msg = `"/usr/share/nginx/html/hello/world" is not found ` +
		`(2: No such file or directory)`
	const extra = `, client: 64.225.101.100, server: gbenson.net, ` +
		`request: "GET /hello/world HTTP/1.1", host: "gbens"n.net", ` +
		`referrer: "http://216.213.58.42:80/v2/"`
	const in = `2024/09/02 10:00:31 [error] 39#39: *606 ` + msg + extra

	me, err := NewTestNginxErrorEvent(in)
	assert.NilError(t, err)

	e, err := unmarshalEvent(me)
	assert.NilError(t, err)
	assert.Equal(t, e.Message().String(), in)

	_, ok := e.(*NginxErrorEvent)
	assert.Assert(t, ok, e.Message())

	assert.DeepEqual(t, e.Message().Fields(), map[string]any{
		"client":   "64.225.101.100",
		"conn":     "606",
		"host":     `gbens"n.net`,
		"level":    "error",
		"message":  msg,
		"pid":      "39",
		"referrer": "http://216.213.58.42:80/v2/",
		"request":  "GET /hello/world HTTP/1.1",
		"server":   "gbenson.net",
		"tid":      "39",
		"time":     "2024/09/02 10:00:31",
	})

	assert.Equal(t, e.Priority(), PriErr)
}
