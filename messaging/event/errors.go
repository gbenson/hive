package event

import "reflect"

// An UnsupportedTypeError is returned by [Marshal] and [Unmarshal]
// when attempting to encode or decode an unsupported value type.
type UnsupportedTypeError struct {
	Type reflect.Type
}

func (e *UnsupportedTypeError) Error() string {
	return "event: unsupported type: " + e.Type.String()
}
