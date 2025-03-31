package util

// ContextKey is a key for use with context.Value.  It's used as a
// pointer so it fits in an interface{} without allocation.
type ContextKey struct {
	name string
}

func NewContextKey(name string) *ContextKey {
	return &ContextKey{name}
}

func (k *ContextKey) String() string {
	return k.name + " context value"
}
