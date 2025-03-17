// Package matrix provides Matrix connectivity for Hive.
package matrix

import (
	"context"
	"errors"
	"io"
	"log"
	"os"
	"path/filepath"

	"maunium.net/go/mautrix"
	"maunium.net/go/mautrix/crypto/cryptohelper"
	"maunium.net/go/mautrix/id"

	"gbenson.net/hive/config"
	"gbenson.net/hive/util"
)

type configKeys struct {
	AccessToken string
	Database    string
	DeviceID    string
	Homeserver  string
	Password    string
	RecoveryKey string
	UserID      string
}

func configKeysFor(s string) configKeys {
	return configKeys{
		AccessToken: s + ".access_token",
		Database:    s + ".database",
		DeviceID:    s + ".device_id",
		Homeserver:  s + ".homeserver",
		Password:    s + ".password",
		RecoveryKey: s + ".recovery_key",
		UserID:      s + ".user_id",
	}
}

type Conn struct {
	mautrix.Client
}

// Dial returns a new connection to the Matrix.
func Dial(configKey string) (*Conn, error) {
	return DialContext(context.Background(), configKey)
}

// DialContext returns a new connection to the Matrix.
func DialContext(ctx context.Context, configKey string) (*Conn, error) {
	if configKey == "" {
		return nil, errors.New("no configKey")
	}
	ck := configKeysFor(configKey)

	c := config.New("matrix")

	if err := c.Read(); err != nil {
		return nil, err
	}

	stateDir, err := util.UserStateDir()
	if err != nil {
		return nil, err
	}
	stateDir = filepath.Join(stateDir, "hive", "matrix")
	c.SetDefault(ck.Database, filepath.Join(stateDir, configKey+".db"))

	c.SetDefault(ck.Homeserver, "matrix.org")
	homeserver := c.GetString(ck.Homeserver)

	c.SetDefault(ck.UserID, id.NewUserID(configKey, homeserver))
	userID := id.UserID(c.GetString(ck.UserID))
	_, homeserver, err = userID.ParseAndValidate()
	if err != nil {
		return nil, err
	}

	accessToken := c.GetString(ck.AccessToken)

	client, err := mautrix.NewClient(homeserver, userID, accessToken)
	if err != nil {
		return nil, err
	}

	conn := &Conn{*client}

	err = conn.init(ctx, c, &ck)
	if err == nil {
		return conn, nil
	}

	defer conn.Close()
	return nil, err
}

func (conn *Conn) init(
	ctx context.Context,
	c *config.Config,
	ck *configKeys,
) error {

	databasePath := c.GetString(ck.Database)
	log.Printf("databasePath: %v", databasePath)
	if err := os.MkdirAll(filepath.Dir(databasePath), 0700); err != nil {
		return err
	}

	helper, err := cryptohelper.NewCryptoHelper(
		&conn.Client,
		[]byte("meow"),
		databasePath,
	)
	if err != nil {
		return err
	}
	conn.Crypto = helper // for conn.Close()

	// Set ck.Password and ck.RecoveryKey for initial login,
	// ck.DeviceID and ck.AccessToken for subsequent connections.
	conn.DeviceID = id.DeviceID(c.GetString(ck.DeviceID))

	if conn.DeviceID == "" || conn.AccessToken == "" {
		helper.LoginAs = &mautrix.ReqLogin{
			Type: mautrix.AuthTypePassword,
			Identifier: mautrix.UserIdentifier{
				Type: mautrix.IdentifierTypeUser,
				User: conn.UserID.Localpart(),
			},
			Password: c.GetString(ck.Password),
		}
	}

	if err := helper.Init(ctx); err != nil {
		return err
	}

	mach := helper.Machine()
	pubkeys := mach.GetOwnCrossSigningPublicKeys(ctx)
	if pubkeys == nil {
		return errors.New("no cross-signing public keys")
	}

	isVerified, err := mach.CryptoStore.IsKeySignedBy(
		ctx,
		conn.UserID,
		mach.GetAccount().SigningKey(),
		conn.UserID,
		pubkeys.SelfSigningKey,
	)
	if err != nil || isVerified {
		return err
	}

	recoveryKey := c.GetString(ck.RecoveryKey)
	if recoveryKey == "" {
		return errors.New("no recovery key")
	}

	keyID, keyData, err := mach.SSSS.GetDefaultKeyData(ctx)
	if err != nil {
		return err
	}
	key, err := keyData.VerifyRecoveryKey(keyID, recoveryKey)
	if err != nil {
		return err
	}
	err = mach.FetchCrossSigningKeysFromSSSS(ctx, key)
	if err != nil {
		return err
	}
	err = mach.SignOwnDevice(ctx, mach.OwnIdentity())
	if err != nil {
		return err
	}
	err = mach.SignOwnMasterKey(ctx)
	if err != nil {
		return err
	}

	return nil
}

// Close closes the connection.
func (c *Conn) Close() error {
	helper, _ := c.Crypto.(io.Closer)
	if helper == nil {
		return nil
	}
	return helper.Close()
}
