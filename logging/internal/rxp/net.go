package rxp

const (
	IPv4Octet = `[012]?\d\d?`
	IPv4Addr  = IPv4Octet +
		`\.` + IPv4Octet +
		`\.` + IPv4Octet +
		`\.` + IPv4Octet
)
