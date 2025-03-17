package matrix

import "errors"

var (
	ErrNoAccessToken      = errors.New("got device ID without access token")
	ErrNoDeviceID         = errors.New("got access token without device ID")
	ErrNoCredentials      = errors.New("no credentials")
	ErrNoCrossSigningKeys = errors.New("no cross-signing keys")
	ErrNoHomeserver       = errors.New("no homeserver")
	ErrNoRecoveryKey      = errors.New("no recovery key")
	ErrNoSyncer           = errors.New("no syncer")
)
