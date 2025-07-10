package spooler

import (
	"bytes"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"gbenson.net/go/logger"
)

// testRequest create a mock [http.Request].
func testRequest(t *testing.T, method string, body any) *http.Request {
	if s, ok := body.(string); ok {
		body = bytes.NewReader([]byte(s))
	}
	r, ok := body.(io.Reader)
	if body != nil && !ok {
		t.Fatalf("%T: unsupported type", body)
	}

	const target = "http://example.com/foo"
	ctx := logger.TestContext(t)
	return httptest.NewRequestWithContext(ctx, method, target, r)
}

// getResponse returns the handler's [http.Response] to the given request.
func getResponse(req *http.Request) *http.Response {
	w := httptest.NewRecorder()
	(&Service{name: "log-spooler"}).ServeHTTP(w, req)
	return w.Result()
}
