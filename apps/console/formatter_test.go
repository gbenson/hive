package console

import (
	"testing"

	"gotest.tools/v3/assert"
)

func TestFormatValue(t *testing.T) {
	for _, tc := range []struct {
		Input any
		Want  string
	}{
		{"hello", "hello"},
		{"hello: world!", `"hello: world!"`},
		//{`hello: "world"`, "`hello: \"world\"`},
		//{"hello: `world`"`, "\"hello: `world`\""},
		//{"`hello`: \"world\"", "\"`hello`: \\\"world\\\""},
		{1751208843252, "1751208843252"},
		{
			map[string]any{
				"a": map[string]any{
					"bc": "def!",
					"g":  map[string]any{},
				},
				"hi":  1751208843252,
				"jkl": "m",
			},
			`{"a":{"bc":"def!","g":{}},"hi":1751208843252,"jkl":"m"}`,
		},
	} {
		assert.Equal(t, formatValue(tc.Input), tc.Want)
	}
}
