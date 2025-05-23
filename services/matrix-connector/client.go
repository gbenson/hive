package matrix

import (
	"context"
	"io"
	"os"
	"path/filepath"
	"time"

	"gbenson.net/go/logger"

	"maunium.net/go/mautrix"
	"maunium.net/go/mautrix/crypto"
	"maunium.net/go/mautrix/crypto/cryptohelper"
	"maunium.net/go/mautrix/event"
	"maunium.net/go/mautrix/id"
)

type Client struct {
	mautrix.Client
	mach *crypto.OlmMachine
}

// Dial returns a new connection to the Matrix.
func Dial(ctx context.Context, o *Options) (*Client, error) {
	if ctx == nil {
		panic("nil context")
	}
	if o == nil {
		panic("nil options")
	}

	mc, err := mautrix.NewClient(
		o.Homeserver,
		id.UserID(o.UserID),
		o.AccessToken,
	)
	if err != nil {
		return nil, err
	}
	mc.Log = *o.Log

	conn := &Client{Client: *mc}
	if err := conn.init(ctx, o); err != nil {
		defer conn.Close()
		return nil, err
	}

	return conn, nil
}

func (conn *Client) init(ctx context.Context, o *Options) error {
	conn.DeviceID = id.DeviceID(o.DeviceID)

	store := o.DatabasePath
	if err := os.MkdirAll(filepath.Dir(store), 0700); err != nil {
		return err
	}

	helper, err := cryptohelper.NewCryptoHelper(
		&conn.Client,
		[]byte("meow"),
		store,
	)
	if err != nil {
		return err
	}
	conn.Crypto = helper

	// Want o.Password and o.RecoveryKey for the initial login,
	// o.DeviceID and o.AccessToken for subsequent connections.
	isLoginFlow := conn.AccessToken == ""
	if isLoginFlow {
		helper.LoginAs = &mautrix.ReqLogin{
			Type: mautrix.AuthTypePassword,
			Identifier: mautrix.UserIdentifier{
				Type: mautrix.IdentifierTypeUser,
				User: conn.UserID.Localpart(),
			},
			Password: o.Password,
		}
	}

	if err := helper.Init(ctx); err != nil {
		return err
	}

	log := conn.Log.Info().
		Str("user_id", conn.UserID.String()).
		Str("device_id", conn.DeviceID.String())
	if isLoginFlow {
		// Log unredacted access token for copying into config.
		log = log.Str("access_token", conn.AccessToken)
	}
	log.Msg("Authenticated")

	conn.mach = helper.Machine()
	pubkeys := conn.mach.GetOwnCrossSigningPublicKeys(ctx)
	if pubkeys == nil {
		return ErrNoCrossSigningKeys
	}

	isVerified, err := conn.mach.CryptoStore.IsKeySignedBy(
		ctx,
		conn.UserID,
		conn.mach.GetAccount().SigningKey(),
		conn.UserID,
		pubkeys.SelfSigningKey,
	)
	if err != nil {
		return err
	}
	if isVerified {
		conn.Log.Info().Msg("Device is verified")
		if o.RecoveryKey != "" {
			conn.Log.Warn().
				Msg("Consider removing your recovery key from the config")
		}
		return nil
	} else {
		conn.Log.Warn().Msg("Device is not verified")
	}

	if o.RecoveryKey == "" {
		return ErrNoRecoveryKey
	}

	// conn.Sync needs to upload keys for verify to work, so we run
	// the verifier in its own goroutine so this function can return
	// and let our caller get on with calling Sync.
	go func() {
		conn.verify(ctx, o.RecoveryKey)
	}()

	return nil
}

func (c *Client) verify(ctx context.Context, recoveryKey string) {
	for {
		if err := c.Verify(ctx, recoveryKey); err != nil {
			c.Log.Err(err).Msg("Verify failed")
			time.Sleep(1 * time.Second)
			continue
		}

		c.Log.Info().Msg("Device is verified")
		c.Log.Warn().
			Msg("Consider removing your recovery key from the config")

		return
	}
}

// Verify verifies the device using a recovery key.
func (c *Client) Verify(ctx context.Context, recoveryKey string) error {
	keyID, keyData, err := c.mach.SSSS.GetDefaultKeyData(ctx)
	if err != nil {
		return err
	}
	key, err := keyData.VerifyRecoveryKey(keyID, recoveryKey)
	if err != nil {
		return err
	}
	if err := c.mach.FetchCrossSigningKeysFromSSSS(ctx, key); err != nil {
		return err
	}
	if err := c.mach.SignOwnDevice(ctx, c.mach.OwnIdentity()); err != nil {
		return err
	}
	if err := c.mach.SignOwnMasterKey(ctx); err != nil {
		return err
	}

	return nil
}

// Close closes the connection.
func (c *Client) Close() error {
	helper, _ := c.Crypto.(io.Closer)
	if helper == nil {
		return nil
	}
	logger.LoggedClose(&c.Log, helper, "database")
	return nil
}

// OnEventType allows callers to be notified when there are new events
// for the given event type. There are no duplicate checks.
func (c *Client) OnEventType(
	eventType event.Type,
	callback mautrix.EventHandler,
) error {
	syncer, ok := c.Syncer.(*mautrix.DefaultSyncer)
	if !ok {
		return ErrNoSyncer
	}
	syncer.OnEventType(eventType, callback)
	return nil
}
