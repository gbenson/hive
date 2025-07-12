package main

import (
	"gbenson.net/hive"
	"gbenson.net/hive/apps/log-analyser"
)

func main() {
	hive.Run(analyser.Main)
}
