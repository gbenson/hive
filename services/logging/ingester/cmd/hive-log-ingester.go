// hive-log-ingester routes systemd journal entries onto the Hive message bus.
package main

import (
	"gbenson.net/hive"
	"gbenson.net/hive/services/logging/ingester"
)

func main() {
	hive.Run(&ingester.Service{})
}
