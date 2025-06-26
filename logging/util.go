package logging

// StringField returns the string value of an event's message field.
func StringField(e Event, k string) string {
	v, _ := e.Message().Fields()[k].(string)
	return v
}
