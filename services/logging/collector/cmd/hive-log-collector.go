// hive-log-collector publishes systemd journal entries onto the Hive
// message bus.
package main

import (
	"gbenson.net/hive"
	"gbenson.net/hive/services/logging/collector"
)

func main() {
	hive.Run(&collector.Service{})
}
