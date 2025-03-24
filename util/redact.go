package util

import "net/url"

// Redacted will be output in logs in place of sensitive information.
const Redacted = "xxxxx"

// RedactURL redacts a URL's userinfo subcomponent, if present.
func RedactURL(s string) string {
	u, err := url.Parse(s)
	if err != nil {
		return Redacted // can't parse? redact everything!
	}
	if u.User == nil {
		return s
	}
	ru := *u
	ru.User = url.User(Redacted)
	return ru.String()
}
