package downgrades

import (
	"strings"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/wrappers"
)

const nginxWebroot = "/usr/share/nginx/html/"

func init() {
	registerDowngrade("nginx-no-such-file", PriInfo, func(e Event) bool {
		_, ok := e.(*NginxErrorEvent)
		if !ok {
			return false
		}

		if e.Priority() != PriErr {
			return false
		}

		s := StringField(e, "message")
		s, _, found := strings.Cut(s, " (2: No such file or directory)")
		if !found {
			return false
		}

		if s, found = strings.CutPrefix(s, `open() "`); found {
			// open() "/path/to/file" failed (2: No such file or directory)
			if s, found = strings.CutSuffix(s, `" failed`); found {
				return pathHasPrefix(s, nginxWebroot)
			}
		} else if s, found = strings.CutSuffix(s, `" is not found`); found {
			// "/path/to/file" is not found (2: No such file or directory)
			if s, found = strings.CutPrefix(s, `"`); found {
				return pathHasPrefix(s, nginxWebroot)
			}
		}
		return false
	})
}
