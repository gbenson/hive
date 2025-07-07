package downgrades

import (
	"path"
	"strings"
)

// pathHasPrefix reports whether p is a regular filesystem path rooted
// in prefix.  Note that the filesystem is **not** inspected, this is
// purely a string manipulation, so keep symbolic links in mind.
func pathHasPrefix(p, prefix string) bool {
	return strings.HasPrefix(p, prefix) && path.Clean(p) == p
}
