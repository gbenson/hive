// hive-log-forwarder routes systemd journal entries onto the Hive message bus.
package main

import (
	"gbenson.net/hive"
	"gbenson.net/hive/services/log-forwarder"
)

func main() {
	hive.Run(&forwarder.Service{})
}
