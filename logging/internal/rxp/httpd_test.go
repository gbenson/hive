package rxp

import (
	"regexp"
	"testing"

	"gotest.tools/v3/assert"
)

func TestCommonLogTimestamp(t *testing.T) {
	rx := regexp.MustCompile("^" + CommonLogTimestamp + "$")
	for _, s := range []string{
		"02/Sep/2024:10:00:31 +0100",
		"13/Sep/2024:10:00:31 +0100",
		"23/Sep/2024:10:00:31 +0100",
		"31/Sep/2024:10:00:31 +0100",
	} {
		assert.Equal(t, rx.FindString(s), s)
	}

	for _, s := range []string{
		" 02/Sep/2024:10:00:31 +0100",
		"02/Sep/2024:10:00:31 +0100 ",
	} {
		assert.Equal(t, rx.FindString(s), "")
	}
}
