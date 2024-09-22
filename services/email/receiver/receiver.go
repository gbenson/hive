package receiver

import (
	"fmt"

	"github.com/emersion/go-imap/v2/imapclient"
	"github.com/gbenson/hive/services/email/receiver/internal/config"
)

type Receiver struct {
	Addr         string
	Username     string
	Password     string
	Inboxes      []string
	ReadingLists []string
	imap         *imapclient.Client
}

func NewReceiver() (*Receiver, error) {
	r := &Receiver{}

	if err := r.configure(); err != nil {
		return nil, err
	}

	c, err := r.dialIMAPS()
	if err != nil {
		return nil, err
	}

	r.imap = c
	return r, nil
}

func (r *Receiver) configure() (err error) {
	key := "email"
	if err = config.Read(key); err != nil {
		return
	}

	key += ".imap."

	var host, port string
	if host, err = config.MustGetString(key + "host"); err != nil {
		return
	}
	if port = config.GetString(key + "port"); port == "" {
		port = "imaps"
	}
	r.Addr = host + ":" + port

	if r.Username, err = config.MustGetString(key + "username"); err != nil {
		return
	}

	if r.Password, err = config.MustGetString(key + "password"); err != nil {
		return
	}

	r.Inboxes = config.GetStringSlice(key + "inboxes")
	r.ReadingLists = config.GetStringSlice(key + "readinglists")
	if len(r.Inboxes) == 0 && len(r.ReadingLists) == 0 {
		return fmt.Errorf("neither %sinboxes nor %sreadinglists are set",
			key, key)
	}

	return nil
}

func (r *Receiver) dialIMAPS() (*imapclient.Client, error) {
	c, err := imapclient.DialTLS(r.Addr, nil)
	if err != nil {
		return nil, err
	}
	if err := c.Login(r.Username, r.Password).Wait(); err != nil {
		c.Close()
		return nil, err
	}
	return c, nil
}

func (r *Receiver) Close() error {
	c := r.imap
	defer c.Close()
	return c.Logout().Wait()
}
