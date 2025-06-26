package event

import "iter"

// Message represents the primary content of a logged event.
type Message interface {
	// String returns the message as text intended to be shown to the
	// user. In most cases this will be the raw text supploed by the
	// originating process, though this isn't enforced.  Note that
	// newline characters are permitted, and ANSI control sequences
	// are not unexpected.
	String() string

	// Fields returns the message as key-value pairs, if available.
	// Fields is an unfiltered, unsorted view of the message for
	// programmatic access; see [Pairs] for an ordered, filtered
	// sequence of key-value pairs intended for message construction.
	// Fields returns nil if the message is unstructured.
	Fields() map[string]any

	// Pairs returns the message as a sequence of key-value pairs
	// suitable for constructing messages for display.  Don't use
	// it to access data, use [Fields] for that.  Pairs returns an
	// empty sequence if the message is unstructured.
	Pairs() iter.Seq2[string, any]
}
