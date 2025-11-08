package integrator

import (
	"errors"
	"fmt"
)

var (
	ErrNoQuestions       = errors.New("no questions")
	ErrPublishBufferFull = errors.New("publish buffer full")
	ErrTooManyQuestions  = errors.New("too many questions")
)

type ConfigError string

func (e ConfigError) Error() string {
	return fmt.Sprintf("unconfigured: %s", string(e))
}

type QuestionError string

func (e QuestionError) Error() string {
	return fmt.Sprintf("unhandled question %q", string(e))
}
