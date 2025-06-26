package logging

// kvp is a key-value pair.
type kvp struct {
	k string
	v any
}

// LoggerTag returns the "net_gbenson_logger" field of an event's
// message field.
func LoggerTag(e Event) string {
	return StringField(e, LoggerTagField)
}

// StringField returns the string value of an event's message field.
func StringField(e Event, k string) string {
	v, _ := e.Message().Fields()[k].(string)
	return v
}
