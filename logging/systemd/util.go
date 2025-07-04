package systemd

import (
	"encoding/base64"
	"strconv"
)

// b64encode returns the standard base64 encoding of b.
func b64encode(b []byte) string {
	return base64.StdEncoding.EncodeToString(b)
}

// clone returns a shallow copy of an object.
func clone[T any](obj *T) *T {
	if obj == nil {
		panic("nil object")
	}
	r := *obj
	return &r
}

// itoa returns the string representation of i in base 10.
func itoa(i int64) string {
	return strconv.FormatInt(i, 10)
}

// utoa returns the string representation of u in base 10.
func utoa(u uint64) string {
	return strconv.FormatUint(u, 10)
}
