package rxp

import (
	"regexp"
	"testing"

	"gotest.tools/v3/assert"
)

func TestIPv4Addr(t *testing.T) {
	rx := regexp.MustCompile("^" + IPv4Addr + "$")
	for _, s := range []string{
		"216.213.58.42",
		"1.0.0.1",
	} {
		assert.Equal(t, rx.FindString(s), s)
	}

	for _, s := range []string{
		" 216.213.58.42",
		"216.213.58.42 ",
		"216.213.58-42",
		"316.213.58.42",
		"216.213.58.4c",
	} {
		assert.Equal(t, rx.FindString(s), "")
	}
}
