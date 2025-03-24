package matrix

import (
	"errors"
	"os"
	"path/filepath"

	"gbenson.net/hive/config"
	"gbenson.net/hive/logger"
	"gbenson.net/hive/util"

	"maunium.net/go/mautrix/id"
)

// DialOptions defaults
const (
	DefaultConfigKey  = "user"
	DefaultHomeserver = "matrix.org"
)

// DialOptions holds the options for Dial and DialContext.
type DialOptions struct {
	// ConfigKey is a ~/.config/hive/matrix.yml entry to source default values from.
	// Defaults to DefaultConfigKey.
	ConfigKey string

	// Log specifies an optional logger to use for logging.
	// TODO(gbenson): Remove this field.
	Log *logger.Logger

	// Homeserver is the homeserver to connect to.  Defaults to the value from
	// UserID, if specified, DefaultHomeserver otherwise.
	Homeserver string

	// UserID is the Matrix user ID to connect as.  Defaults to :ConfigKey@HomeServer.
	UserID string

	// AccessToken is a previously-obtained access token to authenticate with.
	AccessToken string

	// DeviceID is the Device ID to use.  This is the thing you're verifying when
	// you verify a session.  Keys are associated with it, and its value is visible
	// unencrypted in encrypted event sources.
	DeviceID string

	// Password to be used to obtain an access token if one isn't supplied.
	Password string

	// DatabasePath is the path to an SQLite database which OlmMachine will use
	// to store Olm and Megolm sessions, user device lists and message indices.
	DatabasePath string

	// RecoveryKey is used during session verification.
	RecoveryKey string
}

func (o *DialOptions) populateForDial() error {
	if err := o.ensureConfigKey(); err != nil {
		return err
	}

	c, ck, err := o.getConfig()
	if err != nil {
		return err
	}

	if err := o.ensureHomeserver(c, ck); err != nil {
		return err
	}
	if err := o.ensureUserID(c, ck); err != nil {
		return err
	}
	if err := o.ensureCredentials(c, ck); err != nil {
		return err
	}
	if err := o.ensureRecoveryKey(c, ck); err != nil {
		return err
	}
	if err := o.ensureDatabasePath(c, ck); err != nil {
		return err
	}

	return nil
}

func (o *DialOptions) ensureConfigKey() error {
	if o.ConfigKey != "" {
		return nil
	}
	if o.UserID == "" {
		o.ConfigKey = DefaultConfigKey
		o.logUpdate("ConfigKey", o.ConfigKey)
		return nil
	}
	username, homeserver, err := id.UserID(o.UserID).ParseAndValidate()
	if err != nil {
		return err
	}
	o.ConfigKey = username
	if o.Homeserver == "" {
		o.Homeserver = homeserver
		o.logUpdate("Homeserver", o.Homeserver)
	}
	return nil
}

func (o *DialOptions) logUpdate(key, value string) {
	o.Log.Debug().
		Str("component", "DialOptions").
		Str("option", key).
		Str("value", value).
		Msg("Set default")
}

func (o *DialOptions) getConfig() (*config.Config, *configKeys, error) {
	c := config.New("matrix")
	if err := c.Read(); err != nil {
		return nil, nil, err
	}
	return c, configKeysFor(o.ConfigKey), nil
}

type configKeys struct {
	AccessToken  string
	DatabasePath string
	DeviceID     string
	Homeserver   string
	Password     string
	RecoveryKey  string
	UserID       string
}

func configKeysFor(s string) *configKeys {
	return &configKeys{
		AccessToken:  s + ".access_token",
		DatabasePath: s + ".database_path",
		DeviceID:     s + ".device_id",
		Homeserver:   s + ".homeserver",
		Password:     s + ".password",
		RecoveryKey:  s + ".recovery_key",
		UserID:       s + ".user_id",
	}
}

func (o *DialOptions) ensureHomeserver(c *config.Config, ck *configKeys) error {
	if o.Homeserver != "" {
		return nil
	}
	if o.UserID == "" {
		c.SetDefault(ck.Homeserver, DefaultHomeserver)
		o.Homeserver = c.GetString(ck.Homeserver)
	} else {
		_, homeserver, err := id.UserID(o.UserID).ParseAndValidate()
		if err != nil {
			return err
		}
		o.Homeserver = homeserver
	}
	if o.Homeserver == "" {
		return ErrNoHomeserver
	}
	o.logUpdate("Homeserver", o.Homeserver)

	return nil
}

func (o *DialOptions) ensureUserID(c *config.Config, ck *configKeys) error {
	if o.UserID != "" {
		return nil
	}

	c.SetDefault(ck.UserID, id.NewUserID(o.ConfigKey, o.Homeserver).String())
	userID := id.UserID(c.GetString(ck.UserID))
	if _, _, err := userID.ParseAndValidate(); err != nil {
		return err
	}

	o.UserID = userID.String()
	o.logUpdate("UserID", o.UserID)

	return nil
}

func (o *DialOptions) ensureCredentials(c *config.Config, ck *configKeys) error {
	if o.AccessToken == "" {
		if s := c.GetString(ck.AccessToken); s != "" {
			o.AccessToken = s
			o.logUpdate("AccessToken", util.Redacted)
		}
	}

	if o.DeviceID == "" {
		if s := c.GetString(ck.DeviceID); s != "" {
			o.DeviceID = s
			o.logUpdate("DeviceID", s)
		}
	}

	if o.AccessToken != "" {
		if o.DeviceID != "" {
			return nil
		}
		return ErrNoDeviceID
	} else if o.DeviceID != "" {
		return ErrNoAccessToken
	}

	if o.Password == "" {
		if s := c.GetString(ck.Password); s != "" {
			o.Password = s
			o.logUpdate("Password", util.Redacted)
		} else {
			return ErrNoCredentials
		}
	}

	return nil
}

func (o *DialOptions) ensureRecoveryKey(c *config.Config, ck *configKeys) error {
	if o.RecoveryKey != "" {
		return nil
	}

	if s := c.GetString(ck.RecoveryKey); s != "" {
		o.RecoveryKey = s
		o.logUpdate("RecoveryKey", util.Redacted)
	}

	return nil
}

func (o *DialOptions) ensureDatabasePath(c *config.Config, ck *configKeys) error {
	if o.DatabasePath != "" {
		return nil
	}

	if s := c.GetString(ck.DatabasePath); s != "" {
		o.setDatabasePath(s, "")
		return nil
	}

	stateDir, err := util.UserStateDir()
	if err != nil {
		return err
	}
	stateDir = filepath.Join(stateDir, "hive", "matrix")

	// Construct a fallback path to use if we don't have a DeviceID.
	localpart, homeserver, err := id.UserID(o.UserID).ParseAndValidate()
	if err != nil {
		return err
	}
	fallbackPath := filepath.Join(stateDir, homeserver, localpart+".db")

	if o.DeviceID == "" {
		o.setDatabasePath(fallbackPath, "")
		return nil
	}

	// Path to prefer if we *do* have a DeviceID.
	preferredPath := filepath.Join(stateDir, o.DeviceID+".db")

	for _, pp := range []struct {
		Path, BetterPath string
	}{
		{preferredPath, ""},
		{fallbackPath, preferredPath},
	} {
		if _, err := os.Stat(pp.Path); err == nil {
			o.setDatabasePath(pp.Path, pp.BetterPath)
			return nil
		} else if !errors.Is(err, os.ErrNotExist) {
			return err
		}
	}

	o.setDatabasePath(fallbackPath, preferredPath)
	return nil
}

func (o *DialOptions) setDatabasePath(path, betterPath string) {
	o.DatabasePath = path
	o.logUpdate("DatabasePath", path)
	if betterPath == "" {
		return
	}
	o.Log.Warn().
		Str("current_path", path).
		Str("preferred_path", betterPath).
		Msg("Consider moving the database")
}
