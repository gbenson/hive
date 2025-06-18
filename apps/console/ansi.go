package console

import (
	"strconv"
	"strings"
)

const (
	CSI    = "\x1B["           // Control Sequence Introducer
	RESET  = CSI + "0m"        // all attributes off
	M_GREY = CSI + "38;5;244m" // mid grey
)

func MidGrey(s string) string {
	return Colors(244, -1, s)
}

func Colors(fg, bg int, s string) string {
	var b strings.Builder

	b.WriteString(CSI)
	if fg >= 0 {
		b.WriteString("38;5;")
		b.WriteString(strconv.Itoa(fg))
	}
	if bg >= 0 {
		if fg >= 0 {
			b.WriteRune(';')
		}
		b.WriteString("48;5;")
		b.WriteString(strconv.Itoa(bg))
	}
	b.WriteRune('m')

	b.WriteString(s)
	b.WriteString(RESET)

	return b.String()
}
