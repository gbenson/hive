package main

import (
	"log"
	"os"

	"github.com/gbenson/hive/services/email/receiver"
)

func main() {
	if err := receiver.Main(); err != nil {
		log.Println("error:", err)
		os.Exit(1)
	}
}
