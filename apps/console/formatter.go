package console

import (
	"fmt"
	"strings"
	"unicode"

	"golang.org/x/crypto/blake2b"

	"gbenson.net/hive/logging"
)

type Formatter struct {
	prettyHostnames map[string]string
}

func (f *Formatter) Format(e logging.Event) string {
	var b builder

	b.WriteTime(e.Time())
	b.WriteSpace()
	b.WriteString(f.colorHostname(e.Hostname()))
	if s := e.ContainerName(); s != "" {
		b.WriteString(f.colorContainerName(s))
	} else {
		b.WriteString(f.colorCommand(e.Command()))
	}

	// Prefer a structured message, if available.
	msg := e.Message()
	pos := b.Len()
	for k, v := range msg.Pairs() {
		s := fmt.Sprintf("%v", v)
		if s == "" {
			continue
		}
		if shouldQuoteFieldValue(s) {
			s = fmt.Sprintf("%q", s)
		}
		b.WriteString(Cyan(" " + k + "="))
		b.WriteString(s)
	}

	// Fall back to unstructured message if not.
	if b.Len() == pos {
		b.WriteSpace()
		b.WriteString(e.Message().String())
	}

	return b.String()
}

func (f *Formatter) colorHostname(s string) string {
	if cached, ok := f.prettyHostnames[s]; ok {
		return cached
	}

	h := blake2b.Sum512([]byte(s))

	// bg alternatives: 38,51,176; 21,25,82; 5,56,76; 0,10,248
	// (see findansi.go for more...)
	fg := int(h[52] ^ h[60])
	bg := int(h[7]^h[63]) ^ 14

	result := Colors(fg, bg, " "+s+" ")
	if f.prettyHostnames == nil {
		f.prettyHostnames = make(map[string]string)
	}
	f.prettyHostnames[s] = result
	return result
}

func (f *Formatter) colorContainerName(s string) string {
	ss, hasPrefix := strings.CutPrefix(s, "hive-")
	if hasPrefix {
		ss, hasSuffix := strings.CutSuffix(ss, "-1")
		if hasSuffix {
			// Hive containers are a pretty green.
			return Colors(76, 28, " "+ss+" ")
		}
	}

	// Non-hive containers are a garish amber.
	return Colors(220, 130, " "+s+" ")
}

func (f *Formatter) colorCommand(s string) string {
	return Colors(248, 238, " "+s+" ")
}

func shouldQuoteFieldValue(s string) bool {
	if strings.ContainsAny(s, "'\"`\\ \t\n\r") {
		return true
	}
	for _, r := range s {
		if strings.ContainsRune("-_.,<>()[]{}:;@#?/|+*&^%$~", r) {
			continue
		}
		if unicode.IsLetter(r) || unicode.IsNumber(r) {
			continue
		}
		return true
	}
	return false
}
