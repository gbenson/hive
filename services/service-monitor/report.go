package monitor

import (
	"regexp"
	"strings"
	"time"

	"gbenson.net/hive/messaging"
	"gbenson.net/hive/service"
)

type ConditionReport struct {
	EventID   string
	Time      time.Time
	Service   string
	Condition string
	Messages  []string
}

func ParseConditionReportEvent(e *messaging.Event) (*ConditionReport, error) {
	var r service.ConditionReport
	if err := e.DataAs(&r); err != nil {
		return nil, err
	}
	return &ConditionReport{
		EventID:   e.ID(),
		Time:      e.Time(),
		Service:   e.Subject(),
		Condition: r.Condition.String(),
		Messages:  r.Messages,
	}, nil
}

var messageRewriter = regexp.MustCompile(`^Service\b`)

// MarshalEvent marshals a tell_user_request event.
func (r *ConditionReport) MarshalEvent() (*messaging.Event, error) {
	msgs := r.Messages

	if len(msgs) == 0 {
		msgs = append(msgs, "Service became "+r.Condition)
	}
	for i, msg := range msgs {
		msgs[i] = messageRewriter.ReplaceAllLiteralString(msg, r.Service)
	}

	e := messaging.NewEvent()
	e.SetID(r.EventID)
	e.SetType("net.gbenson.hive.tell_user_request")
	e.SetTime(r.Time)
	e.SetData("application/json", strings.Join(msgs, "\n"))

	return e, nil
}
