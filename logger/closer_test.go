package logger

import "testing"

func TestNounVerbToDoingDone(t *testing.T) {
	for _, tc := range []struct {
		noun        string
		verb        []string
		doing, done string
	}{
		{"file thing", []string{}, "Closing file thing", "File thing closed"},
		{"service", []string{"stop"}, "Stopping service", "Service stopped"},
		{"throp", []string{"funt"}, "Funting throp", "Throp funted"},
	} {
		t.Run(tc.doing, func(t *testing.T) {
			doing, done := nounVerbToDoingDone(tc.noun, tc.verb)
			expect(t, doing, tc.doing)
			expect(t, done, tc.done)
		})
	}
}

func expect[T comparable](t *testing.T, got, want T) {
	t.Helper()
	if got == want {
		return
	}
	t.Errorf("want: %v, got: %v", want, got)
}
