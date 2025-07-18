package event

// LoggerTagField is a field that can be added to structured log
// entries to avoid parsers having to guess how they should be parsed.
const LoggerTagField = "net_gbenson_logger"

// LoggerTag returns the value of the "net_gbenson_logger" field of a
// structured event's message.
func LoggerTag(e Event) string {
	return StringField(e, LoggerTagField)
}

// StringField returns the string value of a field in a structured
// event's message.
func StringField(e Event, k string) string {
	v, _ := Field(e, k).(string)
	return v
}

// Field returns the value of a field in a structured event's message.
func Field(e Event, k string) any {
	return e.Message().Fields()[k]
}

// PriorityFromHTTPStatus returns an appropriate syslog severity level
// for an HTTP access log event returning the given HTTP status code.
func PriorityFromHTTPStatus(code int) Priority {
	if code < 500 {
		if code >= 100 {
			return PriInfo
		}
	} else if code < 600 {
		return PriWarning
	}
	return PriErr
}
