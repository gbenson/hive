package forwarder

import "github.com/google/uuid"

func randomUUID() (string, error) {
	u, err := uuid.NewRandom()
	return u.String(), err
}
