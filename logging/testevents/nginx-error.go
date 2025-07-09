package testevents

import (
	"encoding/json"
	"strings"

	messaging_event "gbenson.net/hive/messaging/event"
)

func NewTestNginxErrorEvent(msg string) (*messaging_event.Event, error) {
	b, err := json.Marshal(&msg)
	if err != nil {
		return nil, err
	}
	s := strings.Replace(nginxErrorEventTemplate, "{{MESSAGE}}", string(b), 1)
	return messaging_event.UnmarshalJSON([]byte(s))
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
