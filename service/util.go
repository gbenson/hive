package service

import (
	"os"
	"path/filepath"

	"gbenson.net/hive/util"
)

// StateDir returns the application-specific subdirectory to use for
// persistent state.  The directory will be created if it does not
// exist, but is not guaranteed to be writable.
func StateDir() (string, error) {
	return stateDir(nil)
}

func stateDir(rsm *RestartMonitor) (string, error) {
	d, err := util.UserStateDir()
	if err != nil {
		if rsm != nil {
			rsm.LogWarning(err)
		}
		d = "/var/lib"
	}
	d = filepath.Join(d, "hive", util.ServiceName())
	if err := os.MkdirAll(d, 0700); err != nil {
		return "", err
	}
	return d, nil
}
