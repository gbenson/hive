package downgrades

import (
	"strings"

	. "gbenson.net/hive/logging/event"
	. "gbenson.net/hive/logging/wrappers"
)

const nginxCacheDir = "/var/cache/nginx/"

func init() {
	registerDowngrade("nginx-buffer-warning", PriInfo, func(e Event) bool {
		_, ok := e.(*NginxErrorEvent)
		if !ok {
			return false
		}

		if e.Priority() != PriWarning {
			return false
		}

		s := StringField(e, "message")
		what, s, found := strings.Cut(s, " is buffered to a temporary file ")
		if !found {
			return false
		}

		s, found = strings.CutSuffix(s, " while reading upstream")
		switch what {
		case "an upstream response":
			if !found {
				return false
			}
		case "a client request body":
			if found {
				return false
			}
		default:
			return false
		}

		return pathHasPrefix(s, nginxCacheDir)
	})
}
