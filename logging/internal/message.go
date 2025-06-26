package internal

import "iter"

type UnstructuredMessage string

func (s UnstructuredMessage) String() string {
	return string(s)
}

func (s UnstructuredMessage) Fields() map[string]any {
	return nil
}

func (s UnstructuredMessage) Pairs() iter.Seq2[string, any] {
	return func(yield func(string, any) bool) {}
}
