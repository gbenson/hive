package service

// An error which has already been logged.
type LoggedError interface {
	error
	LoggedError() // no-op function to distinguish from other errors.
}

type loggedError struct {
	err error
}

func (e *loggedError) LoggedError() {}

func (e *loggedError) Error() string {
	return "previously logged error: " + e.err.Error()
}

func (e *loggedError) Unwrap() error {
	return e.err
}

// IsLoggedError reports whether an error is a LoggedError.
func IsLoggedError(err error) bool {
	_, result := err.(LoggedError)
	return result
}
