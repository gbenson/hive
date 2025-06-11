// hive-log-forwarder routes log entries from logspout onto the message bus.
package main

import (
	"gbenson.net/hive"
	"gbenson.net/hive/services/logspout/forwarder"
)

func main() {
	hive.Run(&forwarder.Service{})
}
