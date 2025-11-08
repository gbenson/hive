// hive-dnstap-integrator publishes dnstap data onto the Hive message
// bus.
package main

import (
	"gbenson.net/hive"
	"gbenson.net/hive/services/dns/tap/integrator"
)

func main() {
	hive.Run(&integrator.Service{})
}
