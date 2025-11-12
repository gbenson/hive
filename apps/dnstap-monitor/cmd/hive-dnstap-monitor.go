// hive-dnstap-monitor prints dns query events as they occur.
package main

import (
	"gbenson.net/hive"
	"gbenson.net/hive/apps/dnstap-monitor"
)

func main() {
	hive.Run(&monitor.Service{})
}
