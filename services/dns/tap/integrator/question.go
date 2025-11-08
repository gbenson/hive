package integrator

import (
	"encoding/json"
	"fmt"

	"github.com/miekg/dns"
)

type Question dns.Question

func (q *Question) Equal(p *Question) bool {
	return p.Qtype == q.Qtype && p.Qclass == q.Qclass && p.Name == q.Name
}

func (q *Question) MarshalJSON() ([]byte, error) {
	return json.Marshal(map[string]string{
		"name":  q.Name,
		"class": dns.Class(q.Qclass).String(),
		"type":  dns.Type(q.Qtype).String(),
	})
}

func (q *Question) String() string {
	return fmt.Sprintf(
		"%s %s %s",
		q.Name,
		dns.Class(q.Qclass).String(),
		dns.Type(q.Qtype).String(),
	)
}
