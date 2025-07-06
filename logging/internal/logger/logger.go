// Package logger provides the internal logger.
package logger

import "gbenson.net/go/logger"

var disabledLogger = logger.New(&logger.Options{Level: "disabled"})

// Logger is used to report errors that would otherwise be silently
// ignored.  Be careful to avoid loops if you enable this!
var Logger = &disabledLogger

// SetLogger specifies an optional logger for reporting errors that
// would otherwise be silently ignored.  Be careful to avoid loops
// when enabling this!
func SetLogger(log *logger.Logger) {
	if log == nil {
		Logger = &disabledLogger
	} else {
		Logger = log
	}
}
