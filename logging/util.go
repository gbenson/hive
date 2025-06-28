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
