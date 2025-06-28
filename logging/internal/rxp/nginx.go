package rxp

const NginxErrorLogTimestamp = `\d{4}/[01]\d/[0-3]\d [012]\d:[0-5]\d:[0-6]\d`

// https://nginx.org/en/docs/ngx_core_module.html#error_log
const NginxErrorLogLevel = `debug|info|notice|warn|error|crit|alert|emerg`

// https://github.com/nginx/nginx/blob/master/src/core/ngx_log.c#L107
const NginxPidTidConn = `(?P<pid>\d+)#(?P<tid>\d+):(?: \*(?P<conn>\d+))?`

const NginxErrorLogEntryPrefix = `^` +
	`(?P<time>` + NginxErrorLogTimestamp + `) ` +
	`\[(?P<level>` + NginxErrorLogLevel + `)\] ` +
	NginxPidTidConn + ` `

const NginxErrorLogEntry = NginxErrorLogEntryPrefix + `(?P<message>.*)$`

const NginxKeyValuePair = `(?P<key>[a-z]+): (?P<value>[^"].*?|".*?")`

const NginxTrailingField = `^` +
	`(?P<message>.*), ` + NginxKeyValuePair +
	`$`
