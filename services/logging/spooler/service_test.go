package spooler

import (
	"io"
	"strings"
	"testing"

	"gotest.tools/v3/assert"
)

// Everything other than POST returns 405 Method Not Allowed.
func TestBadMethod(t *testing.T) {
	resp := getResponse(testRequest(t, "GET", nil))
	b, _ := io.ReadAll(resp.Body)
	body := string(b)
	assert.Assert(t, strings.HasPrefix(body, "405 Method Not Allowed"), body)
	assert.Equal(t, resp.Header.Get("Connection"), "close")
}

// Requests without credentials return 400 Bad Request.
func TestNoContentType(t *testing.T) {
	resp := getResponse(testRequest(t, "POST", nil))
	b, _ := io.ReadAll(resp.Body)
	body := string(b)
	assert.Assert(t, strings.HasPrefix(body, "400 Bad Request"), body)
}

// Requests with the wrong content type return 400 Bad Request.
func TestBadContentType(t *testing.T) {
	req := testRequest(t, "POST", "u=x&p=y")
	req.Header.Set("Content-Type", "application/json")
	resp := getResponse(req)
	b, _ := io.ReadAll(resp.Body)
	body := string(b)
	assert.Assert(t, strings.HasPrefix(body, "400 Bad Request"), body)
}

// Requests without both username and password return 400 Bad Request.
func TestNoCredentials(t *testing.T) {
	for _, body := range []string{"", "u=x", "p=y", "u=x&q=y", "v=x&p=y"} {
		t.Log(body)
		req := testRequest(t, "POST", body)
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		resp := getResponse(req)
		b, _ := io.ReadAll(resp.Body)
		body = string(b)
		assert.Assert(t, strings.HasPrefix(body, "400 Bad Request"), body)
	}
}

// Requests with both username and password return 503 Service Unavailable.
func TestServiceUnavailable(t *testing.T) {
	req := testRequest(t, "POST", "u=x&p=y")
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	resp := getResponse(req)
	b, _ := io.ReadAll(resp.Body)
	body := string(b)
	assert.Assert(t, strings.HasPrefix(body, "50"), body)
}
