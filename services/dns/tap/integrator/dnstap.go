package integrator

import "time"

// Partially decoded "net.gbenson.hive.dnstap_event" CloudEvent payload.
type dnstap struct {
	Type     string        `json:"type"`
	Identity string        `json:"identity"`
	Message  dnstapMessage `json:"message"`
}

// Partially decoded Dnstap.Message.
type dnstapMessage struct {
	Type         string    `json:"type"`
	QueryTime    time.Time `json:"query_time"`
	QueryIP      string    `json:"query_address"`
	QueryHW      string    `json:"query_hwaddr"`
	QueryMessage []byte    `json:"query_message"`
}
