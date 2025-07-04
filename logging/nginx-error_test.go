package logging

import (
	"encoding/json"
	"strings"
	"testing"

	"gbenson.net/hive/messaging"
	"gotest.tools/v3/assert"

	. "gbenson.net/hive/logging/event"
)

func TestBasicNotice(t *testing.T) {
	const in = `2024/09/02 10:00:31 [notice] 1#1: hello world`

	me, err := newTestNginxErrorEvent(in)
	assert.NilError(t, err)

	e, err := UnmarshalEvent(me)
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

	me, err := newTestNginxErrorEvent(in)
	assert.NilError(t, err)

	e, err := UnmarshalEvent(me)
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

	me, err := newTestNginxErrorEvent(in)
	assert.NilError(t, err)

	e, err := UnmarshalEvent(me)
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

	me, err := newTestNginxErrorEvent(in)
	assert.NilError(t, err)

	e, err := UnmarshalEvent(me)
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

func newTestNginxErrorEvent(msg string) (*messaging.Event, error) {
	b, err := json.Marshal(&msg)
	if err != nil {
		return nil, err
	}
	s := strings.Replace(nginxErrorEventTemplate, "{{MESSAGE}}", string(b), 1)
	return messaging.NewEventFromJSON([]byte(s))
}

const nginxErrorEventTemplate = `{
  "specversion": "1.0",
  "id": "BLAKE2b:1a/b9OyoBottWL0j0Kf+vcvY8IHeoTQlsUcECB/jWO4",
  "source": "https://gbenson.net/hive/services/log-collector",
  "type": "net.gbenson.hive.systemd_journal_event",
  "datacontenttype": "application/json",
  "time": "2025-06-27T07:33:55.257189906Z",
  "data": {
    "realtime_usec": 1751009634906660,
    "monotonic_usec": 1931361950197,
    "fields": {
      "CONTAINER_ID": "9f0911fb18d7",
      "CONTAINER_ID_FULL":
        "9f0911fb18d72d3bf1f18f4b062d176e2f59b3588b7ee5b053e91348a10f9a90",
      "CONTAINER_LOG_EPOCH":
        "ae142c5751bb96103d9289521f8cb6e6dedf856b44f3e73bbf13e266c489249b",
      "CONTAINER_LOG_ORDINAL": "712",
      "CONTAINER_NAME": "hive-nginx-ingress-1",
      "CONTAINER_TAG": "9f0911fb18d7",
      "IMAGE_NAME": "nginx",
      "MESSAGE": {{MESSAGE}},
      "PRIORITY": "3",
      "SYSLOG_IDENTIFIER": "9f0911fb18d7",
      "SYSLOG_TIMESTAMP": "2025-06-27T07:33:54.906434289Z",
      "_BOOT_ID": "27fbd0a3c26945e28624dad56044f8fe",
      "_CAP_EFFECTIVE": "1ffffffffff",
      "_CMDLINE":
        "/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock",
      "_COMM": "dockerd",
      "_EXE": "/usr/bin/dockerd",
      "_GID": "0",
      "_HOSTNAME": "box1",
      "_MACHINE_ID": "b7ae3b30d3284b1dacb78ec9b966f531",
      "_PID": "559660",
      "_RUNTIME_SCOPE": "system",
      "_SELINUX_CONTEXT": "unconfined\n",
      "_SOURCE_REALTIME_TIMESTAMP": "1751009634906579",
      "_SYSTEMD_CGROUP": "/system.slice/docker.service",
      "_SYSTEMD_INVOCATION_ID": "4447f22c48b24b0fb5de0d9827e85483",
      "_SYSTEMD_SLICE": "system.slice",
      "_SYSTEMD_UNIT": "docker.service",
      "_TRANSPORT": "journal",
      "_UID": "0"
    }
  }
}`
