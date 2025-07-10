// hive-log-spooler routes systemd journal entries onto the Hive message bus.
package main

import (
	"gbenson.net/hive"
	"gbenson.net/hive/services/logging/spooler"
)

func main() {
	hive.Run(&spooler.Service{})
}
