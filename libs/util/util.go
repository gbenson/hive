// Package util provides utility functions for Hive libraries and services.
package util

import (
	"errors"
	"os"
	"path/filepath"
)

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
