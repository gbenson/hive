package logging

import "github.com/rs/zerolog"

// zerologPriorityMap maps zerolog logging levels to syslog severity
// levels.  https://pkg.go.dev/github.com/rs/zerolog#pkg-variables
var zerologPriorityMap priorityMap = priorityMap{
	zerolog.LevelTraceValue: PriDebug,
	zerolog.LevelDebugValue: PriDebug,
	zerolog.LevelInfoValue:  PriInfo,
	zerolog.LevelWarnValue:  PriWarning,
	zerolog.LevelErrorValue: PriErr,
	zerolog.LevelFatalValue: PriCrit,
	zerolog.LevelPanicValue: PriCrit,
}
