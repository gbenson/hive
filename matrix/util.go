package matrix

import "gbenson.net/hive/util"

// mask returns a masked version of s suitable for printing and logging.
func mask(s string) string {
	return util.MaskSep(s, "_")
}
