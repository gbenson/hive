// Package util provides common utilities for Hive libraries and services.
package util

import (
	"errors"
	"log"
	"os"
	"path/filepath"
	"strings"
)

const DefaultServiceName = "unknown-service"

// ServiceName returns the kebab-case name of the Hive service this
// executable provides.
func ServiceName() string {
	name, err := os.Executable()
	if err != nil {
		log.Println("WARNING:", err)
		return DefaultServiceName
	}
	name, _ = strings.CutPrefix(filepath.Base(name), "hive-")
	if name == "" {
		return DefaultServiceName
	}
	return name
}

// ServiceNameURL returns an absolute URL which can be used as an
// identifier for the Hive service this executable provides.
func ServiceNameURL() string {
	return "https://gbenson.net/hive/services/" + ServiceName()
}

// UserStateDir returns the default root directory to use for
// user-specific state files. Users should create their own
// application-specific subdirectory within this one and use that.
//
// On Unix systems, it returns $XDG_STATE_HOME as specified by
// https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
// if non-empty, else $HOME/.local/state.
//
// If the location cannot be determined (for example, $HOME is not defined) or
// the path in $XDG_STATE_HOME is relative, then it will return an error.
func UserStateDir() (string, error) {
	dir := os.Getenv("XDG_STATE_HOME")
	if dir == "" {
		dir = os.Getenv("HOME")
		if dir == "" {
			return "", errors.New("neither $XDG_STATE_HOME nor $HOME are defined")
		}
		dir = filepath.Join(dir, ".local", "state")
	} else if !filepath.IsAbs(dir) {
		return "", errors.New("path in $XDG_STATE_HOME is relative")
	}

	return dir, nil
}
