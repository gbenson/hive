// hive-matrix-connector sends and receives Matrix events.
package main

import (
	"gbenson.net/hive"
	"gbenson.net/hive/services/matrix-connector"
)

func main() {
	hive.Run(&matrix.Service{})
}
