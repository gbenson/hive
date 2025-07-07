package wrappers

import (
	"testing"

	"gotest.tools/v3/assert"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/testevents"
)

func TestAuthenticated(t *testing.T) {
	const in = `216.213.58.42 - gbenson` +
		` 02/Sep/2024:10:00:31 +0100` +
		` "GET /index.php" 200`

	me, err := NewTestNginxErrorEvent(in)
	assert.NilError(t, err)

	le, err := unmarshalEvent(me)
	assert.NilError(t, err)
	assert.Equal(t, le.Message().String(), in)

	e, ok := le.(*PHPFPMAccessEvent)
	assert.Assert(t, ok, e.Message())

	const wantTime = "2024-09-02 09:00:31 +0000 UTC"
	assert.Equal(t, e.Timestamp.UTC().String(), wantTime)
	assert.Equal(t, e.RemoteAddr, "216.213.58.42")
	assert.Equal(t, e.RemoteUser, "gbenson")
	assert.Equal(t, e.Method, "GET")
	assert.Equal(t, e.RequestURI, "/index.php")
	assert.Equal(t, e.StatusCode, 200)

	assert.Equal(t, le.Priority(), PriInfo)
}
