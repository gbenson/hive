// Package logging provides centralized logging services for Hive.
package logging

import "gbenson.net/go/logger"

// Logger is used to report errors that would otherwise be ignored.
// Be careful to avoid loops if you enable this!
var disabledLogger = logger.New(&logger.Options{Level: "disabled"})
var Logger = &disabledLogger
