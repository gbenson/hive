package internal

import (
	"github.com/rs/zerolog"

	. "gbenson.net/hive/logging/event"
)

// ZerologPriorityMap maps zerolog logging levels to syslog severity
// levels.  https://pkg.go.dev/github.com/rs/zerolog#pkg-variables
var ZerologPriorityMap = PriorityMap{
	zerolog.LevelTraceValue: PriDebug,
	zerolog.LevelDebugValue: PriDebug,
	zerolog.LevelInfoValue:  PriInfo,
	zerolog.LevelWarnValue:  PriWarning,
	zerolog.LevelErrorValue: PriErr,
	zerolog.LevelFatalValue: PriCrit,
	zerolog.LevelPanicValue: PriCrit,
}
