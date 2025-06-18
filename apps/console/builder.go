package console

import (
	"strings"
	"time"
)

type builder struct {
	strings.Builder
}

func (b *builder) WriteSpace() {
	b.WriteRune(' ')
}

func (b *builder) WriteTime(t time.Time) {
	s := t.In(time.Local).Format("2006-01-02 15:04:05.000000")

	s, frac, gotFrac := strings.Cut(s, ".")

	b.WriteString(s)
	if gotFrac {
		b.WriteString(MidGrey("." + frac))
	}
}
