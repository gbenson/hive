package util

import "fmt"

// A panic which was recovered.
type RecoveredPanicError interface {
	error
	RecoveredPanicError() // no-op function to distinguish from other errors.
}

// NewRecoveredPanicError returns, as an error, a new [RecoveredPanicError].
func NewRecoveredPanicError(v any) error {
	err, _ := v.(error)
	if err == nil {
		err = fmt.Errorf("%v", v)
	}
	return &recoveredPanicError{err}
}

type recoveredPanicError struct {
	err error
}

func (e *recoveredPanicError) RecoveredPanicError() {}

func (e *recoveredPanicError) Error() string {
	return "panic: " + e.err.Error()
}

func (e *recoveredPanicError) Unwrap() error {
	return e.err
}

// IsRecoveredPanicError reports whether an error is a RecoveredPanicError.
func IsRecoveredPanicError(err error) bool {
	_, result := err.(RecoveredPanicError)
	return result
}
