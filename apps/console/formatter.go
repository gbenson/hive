package console

import (
	"strings"

	"golang.org/x/crypto/blake2b"

	"gbenson.net/hive/logging"
)

type Formatter struct {
	prettyHostnames map[string]string
}

func (f *Formatter) Format(e *logging.Event) string {
	var b builder

	b.WriteTime(e.Time())
	b.WriteSpace()
	b.WriteString(f.colorHostname(e.Hostname()))
	if s := e.ContainerName(); s != "" {
		b.WriteString(f.colorContainerName(s))
	} else {
		b.WriteString(f.colorCommand(e.Command()))
	}
	b.WriteSpace()
	b.WriteString(e.RawMessage())

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
