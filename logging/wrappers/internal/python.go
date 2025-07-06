package internal

import . "gbenson.net/hive/logging/event"

// PythonPriorityMap maps Python logging levels to syslog severity
// levels.  https://docs.Python.org/3/library/logging.html#levels
var PythonPriorityMap = PriorityMap{
	"CRITICAL": PriCrit,
	"ERROR":    PriErr,
	"WARNING":  PriWarning,
	"INFO":     PriInfo,
	"DEBUG":    PriDebug,
}
