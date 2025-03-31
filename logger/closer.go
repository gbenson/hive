package logger

import (
	"fmt"
	"io"
	"strings"
)

// LoggedClose wraps an [io.Closer] so it logs errors that would
// otherwise be silently dropped if the closer was invoked as a
// deferred function.
func LoggedClose(log *Logger, c io.Closer, noun string, verb ...string) {
	var doing, done string

	defer func() {
		if err := c.Close(); err != nil {
			log.Err(err).Msg(doing)
		} else {
			log.Debug().Msg(done)
		}
	}()

	doing, done = nounVerbToDoingDone(noun, verb)
	log.Debug().Msg(doing)
}

func nounVerbToDoingDone(noun string, verbs []string) (doing, done string) {
	var verb string
	if len(verbs) > 0 {
		verb = verbs[0]
	}
	if verb == "" {
		verb = "close"
	}
	lasti := len(verb) - 1
	lastc := string(verb[lasti])

	switch lastc {
	case "e":
		verb = verb[:lasti]
	case "p":
		verb += lastc
	}

	doing = fmt.Sprintf("%sing %s", capitalize(verb), noun)
	done = fmt.Sprintf("%s %sed", capitalize(noun), verb)
	return
}

func capitalize(s string) string {
	p := strings.Fields(s)
	if len(p) < 1 {
		return "What??"
	}
	p[0] = strings.Title(p[0])
	return strings.Join(p, " ")
}
