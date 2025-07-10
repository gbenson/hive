package spooler

import (
	"fmt"
	"net/http"
)

type HTTPError int

func (e HTTPError) Error() string {
	return e.Status()
}

func (e HTTPError) Status() string {
	return fmt.Sprintf("%d %s", e.StatusCode(), e.StatusText())
}

func (e HTTPError) StatusCode() int {
	return int(e)
}

func (e HTTPError) StatusText() string {
	return http.StatusText(e.StatusCode())
}

func (e HTTPError) serveHTTP(w http.ResponseWriter, r *http.Request) error {
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.Header().Set("Connection", "close")
	w.WriteHeader(e.StatusCode())
	_, err := w.Write([]byte(e.Status() + "\n"))
	return err
}
