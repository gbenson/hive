package console

import (
	"strings"
	"time"
)

type Builder struct {
	strings.Builder
}

func (b *Builder) WriteSpace() {
	b.WriteRune(' ')
}

func (b *Builder) WriteTime(t time.Time) {
	s := t.In(time.Local).Format("2006-01-02 15:04:05.000000")

	s, frac, gotFrac := strings.Cut(s, ".")

	b.WriteString(s)
	if gotFrac {
		b.WriteString(MidGrey("." + frac))
	}
}
