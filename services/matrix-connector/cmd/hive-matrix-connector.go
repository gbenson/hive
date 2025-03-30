// hive-matrix-connector sends and receives Matrix events.
package main

import (
	"gbenson.net/hive/service"
	impl "gbenson.net/hive/services/matrix-connector"
)

func main() {
	service.Run(&impl.Service{})
}
