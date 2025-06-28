// Package rxparser implements parsing strings using regular expressions.
package rxparser

import (
	"errors"
	"regexp"
	"strconv"
)

// RegexpParser uses regular expressions with named subexpressions
// to parse strings into key-value pair mappings.
type RegexpParser struct {
	rx    *regexp.Regexp
	names []string
}

// New creates a RegexpParser from a compiled regular expression.
func New(rx *regexp.Regexp) (*RegexpParser, error) {
	sxn := rx.SubexpNames()
	if len(sxn) < 2 {
		return nil, errors.New("no subexpressions")
	}
	return &RegexpParser{rx, sxn}, nil
}

// Compile parses a regular expression and returns, if successful,
// a RegexpParser that can be used to parse strings into key-value
// pair mappings.
func Compile(str string) (*RegexpParser, error) {
	rx, err := regexp.Compile(str)
	if err != nil {
		return nil, err
	}
	return New(rx)
}

// MustCompile is like [Compile] but panics if the expression cannot
// be parsed.  It simplifies safe initialization of global variables
// holding compiled regular expressions.
func MustCompile(str string) *RegexpParser {
	rxp, err := Compile(str)
	if err != nil {
		panic(`rxp: Compile(` + quote(str) + `): ` + err.Error())
	}
	return rxp
}

// quote was lifted from go1.24.4/src/regexp/regexp.go
func quote(s string) string {
	if strconv.CanBackquote(s) {
		return "`" + s + "`"
	}
	return strconv.Quote(s)
}

// ParseString returns a key-value pair mapping of all subexpression
// matches found in the given string.  A return value of nil indicates
// no match.
func (p *RegexpParser) ParseString(s string) map[string]string {
	vv := p.rx.FindStringSubmatch(s)
	if len(vv) == 0 {
		return nil
	}

	kk := p.names
	m := make(map[string]string)
	for i, v := range vv {
		if v == "" {
			continue // no empties
		}
		m[kk[i]] = v
	}
	return m
}
