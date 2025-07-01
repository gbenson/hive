package logging

import . "gbenson.net/hive/logging/event"

// pythonPriorityMap maps Python logging levels to syslog severity
// levels.  https://docs.Python.org/3/library/logging.html#levels
var pythonPriorityMap priorityMap = priorityMap{
	"CRITICAL": PriCrit,
	"ERROR":    PriErr,
	"WARNING":  PriWarning,
	"INFO":     PriInfo,
	"DEBUG":    PriDebug,
}
