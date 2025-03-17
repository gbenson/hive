package util

import "strings"

// Mask returns a masked version of a secret, for printing, logging etc.
// Masking uses the same algorithm as GitHub actions, where each masked
// word separated by whitespace is replaced with the "*" character, so
// e.g. `Mask("Mona The Octocat")` returns "***".
//
// Based on https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/workflow-commands-for-github-actions#masking-a-value-in-a-log
func Mask(s string) string {
	return mask(strings.Fields(s))
}

// MaskSep works like Mask, but it splits on sep rather than whitespace,
// so e.g. `MaskSep("Hive_is_the_best!", "_")` returns "****".
func MaskSep(s, sep string) string {
	return mask(strings.Split(s, sep))
}

func mask(elems []string) string {
	for i, _ := range elems {
		elems[i] = "*"
	}
	return strings.Join(elems, "")
}
