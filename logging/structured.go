package logging

import (
	"iter"
	"maps"
	"slices"
)

// sortedPairs iterates over e.Fields(), with the field "message" or
// "msg" first, and everything else sorted alphabetically by name
// afterwards.
func sortedPairs(e Event) iter.Seq2[string, any] {
	return func(yield func(string, any) bool) {
		msg := e.Message().Fields()

		// Output any "message" component first, if present.
		var hoisted string
		for _, k := range []string{"message", "msg"} {
			v := StringField(e, k)
			if v == "" {
				continue
			}
			if !yield(k, v) {
				return
			}
			hoisted = k
			break
		}

		keys := slices.Sorted(maps.Keys(msg))
		for _, k := range keys {
			if k == hoisted {
				continue
			}
			if !yield(k, msg[k]) {
				return
			}
		}
	}
}

// omitPairs returns a function which removes all kk from seq.
func omitPairs(kk ...string) func(iter.Seq2[string, any]) iter.Seq2[string, any] {
	return func(seq iter.Seq2[string, any]) iter.Seq2[string, any] {
		return func(yield func(string, any) bool) {
			for k, v := range seq {
				if slices.Contains(kk, k) {
					continue
				}
				if !yield(k, v) {
					return
				}
			}
		}
	}
}
