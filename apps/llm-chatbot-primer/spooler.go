package primer

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"golang.org/x/term"

	"gbenson.net/go/dfmt"
	"gbenson.net/go/logger"
	"gbenson.net/hive/config"
	"gbenson.net/hive/logging"
	le "gbenson.net/hive/logging/event"
)

var preJSONPrefixParts = []string{
    "\x1B[90m<nil>\x1B[0m ",
    "\x1B[32mINF\x1B[0m ",
    "\x1B[1mReceived\x1B[0m \x1B[36mevent=\x1B[0m",
}

func Main(ctx context.Context) error {
	log := logger.Ctx(ctx)
	logging.SetLogger(log)

	cfg := config.New("log-analyser")

	if err := cfg.Read(); err != nil {
		return err
	}

	b, err := json.Marshal(cfg.GetStringMap("log_analyser"))
	if err != nil {
		return err
	}

	var ep logging.SpoolerEndpoint
	if err := json.Unmarshal(b, &ep); err != nil {
		return err
	}

	spooler := logging.NewSpooler(ctx, &ep)
	defer logger.LoggedClose(log, spooler, "spooler")

loop:
	for spooler.Spool() {
		entry := spooler.Event()
		if !strings.HasPrefix(entry.ContainerName(), "hive-matrix-connector-") {
			continue
		}
		if fields := entry.Message().Fields(); fields != nil {
			event, _ := fields["event"].(map[string]any)
			if event == nil {
				continue
			}
			if err := process(ctx, entry, event); err != nil {
				return err
			}
			continue
		}

		// Old-style (pre-JSON) log event
		msg := entry.Message().String()
		for _, prefix := range preJSONPrefixParts {
			var found bool
			if msg, found = strings.CutPrefix(msg, prefix); !found {
				continue loop
			}
		}

		var event map[string]any
		if err := json.Unmarshal([]byte(msg), &event); err != nil {
			return err
		}
		if err := process(ctx, entry, event); err != nil {
			return err
		}
	}
	if err := spooler.Err(); err != nil {
		return err
	}

	return nil
}

func process(ctx context.Context, entry le.Event, event map[string]any) error {
	typ, _ := event["type"].(string)
	if typ != "m.room.message" {
		if typ != "m.reaction" {
			logger.Ctx(ctx).Warn().
				Str("issue", "type").
				Interface("event", event).
				Msg("")
		}
		return nil
	}

	content, _ := event["content"].(map[string]any)
	if content == nil {
		logger.Ctx(ctx).Warn().
			Str("issue", "content").
			Interface("event", event).
			Msg("")
		return nil
	}

	msgtype, _ := content["msgtype"].(string)
	if msgtype != "m.text" {
		if msgtype != "m.image" {
			logger.Ctx(ctx).Warn().
				Str("issue", "msgtype").
				Interface("event", event).
				Msg("")
		}
		return nil
	}

	body, _ := content["body"].(string)
	if body == "" {
		logger.Ctx(ctx).Warn().
			Str("issue", "body").
			Interface("event", event).
			Msg("")
		return nil
	}

	if width, _, err := term.GetSize(int(os.Stderr.Fd())); err == nil {
		s := dfmt.FormatValue(body)
		if len(s) > 2 {
			if c := s[0]; (c == '"' || c == '`') && s[len(s)-1] == c {
				s = s[1:len(s)-1]
			}
		}
		if width > 20 && len(s) > width {
			s = s[:width-3] + "..."
		}
		fmt.Fprintf(os.Stderr, "\x1B[34m%s\x1B[0m\n", s)
	}

	b, err := json.Marshal(event)
	if err != nil {
		return err
	}

	fmt.Println(string(b))
	return nil
}
