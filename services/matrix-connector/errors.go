package matrix

import "errors"

var (
	ErrBadRequest         = errors.New("bad request")
	ErrNoAccessToken      = errors.New("got device ID without access token")
	ErrNoCredentials      = errors.New("no credentials")
	ErrNoCrossSigningKeys = errors.New("no cross-signing keys")
	ErrNoDeviceID         = errors.New("got access token without device ID")
	ErrNoEventID          = errors.New("no event ID")
	ErrNoHomeserver       = errors.New("no homeserver")
	ErrNoRecoveryKey      = errors.New("no recovery key")
	ErrNoRoomID           = errors.New("no room ID")
	ErrNoSyncer           = errors.New("no syncer")
)
