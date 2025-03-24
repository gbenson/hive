// hive-service-monitor collates service condition reports into user messages.
package main

import (
	"gbenson.net/hive/service"
	impl "gbenson.net/hive/services/service-monitor"
)

func main() {
	service.Run(&impl.Service{})
}
