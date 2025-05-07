package util

import (
	"log"
	"os"
	"path/filepath"
	"strings"
)

// DefaultServiceName will be returned by ServiceName if no better
// alternative can be determined.
const DefaultServiceName = "unknown-service"

// serviceName is the cached return value of ServiceName.
var serviceName string

// ServiceName returns the kebab-case name of the Hive service this
// executable provides.
func ServiceName() string {
	if serviceName == "" {
		serviceName = serviceNameFromExecutable()
	}
	if serviceName == "" {
		serviceName = DefaultServiceName
	}
	return serviceName
}

func serviceNameFromExecutable() string {
	name, err := os.Executable()
	if err != nil {
		log.Println("WARNING:", err)
		return ""
	}
	name, _ = strings.CutPrefix(filepath.Base(name), "hive-")
	return name
}
