// hive-dnstap-collector publishes dnstap data onto the Hive message
// bus.
package main

import (
	"gbenson.net/hive"
	"gbenson.net/hive/services/dns/tap/collector"
)

func main() {
	hive.Run(&collector.Service{})
}
