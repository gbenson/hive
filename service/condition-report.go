package service

import (
	"encoding/json"
	"fmt"
	"strings"
)

type Condition int

const (
	ConditionHealthy Condition = iota
	ConditionDubious
	ConditionInError
	ConditionUnmonitored
)

type ConditionReport struct {
	Condition Condition `json:"condition"`
	Messages  []string  `json:"messages,omitempty"`
}

func (c Condition) String() string {
	switch c {
	case ConditionHealthy:
		return "healthy"
	case ConditionDubious:
		return "dubious"
	case ConditionInError:
		return "in_error"
	case ConditionUnmonitored:
		return "unmonitored"
	default:
		return fmt.Sprintf("condition-%d", c)
	}
}

func (c Condition) MarshalJSON() ([]byte, error) {
	return json.Marshal(c.String())
}

func (c *Condition) UnmarshalJSON(b []byte) error {
	var s string
	if err := json.Unmarshal(b, &s); err != nil {
		return err
	}

	switch strings.ToLower(s) {
	case "healthy":
		*c = ConditionHealthy
	case "dubious":
		*c = ConditionDubious
	case "in_error":
		*c = ConditionInError
	case "unmonitored":
		*c = ConditionUnmonitored
	default:
		return fmt.Errorf("unexpected condition %q", s)
	}

	return nil
}
