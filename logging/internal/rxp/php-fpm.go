package rxp

const PHPFPMAccessLogEntry = `^(?P<remote_addr>` + IPv4Addr + `)` +
	` -` +
	` (?P<remote_user>\S+)` +
	` (?P<timestamp>` + CommonLogTimestamp + `)` +
	` "(?P<method>\S+)` +
	` (?P<request_uri>/.*)` +
	`" (?P<status>` + HTTPStatusCode + `)$`
