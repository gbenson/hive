package systemd

import "fmt"

// A checksum failed.
type DigestError struct {
	Got, Want string
}

func (e *DigestError) Error() string {
	return fmt.Sprintf("invalid digest: got %q, want %q", e.Got, e.Want)
}
