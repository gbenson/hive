// hive-console prints logged events as they occur.
package main

import (
	"gbenson.net/hive"
	"gbenson.net/hive/apps/console"
)

func main() {
	hive.Run(&console.Service{})
}
