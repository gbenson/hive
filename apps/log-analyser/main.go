package analyser

import (
	"context"
	"encoding/json"
	"fmt"
	"maps"
	"reflect"
	"slices"

	"gbenson.net/go/logger"
	"gbenson.net/hive/config"
	"gbenson.net/hive/logging"
)

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

	hist := make(map[string]int)

	spooler := logging.NewSpooler(ctx, &ep)
	defer logger.LoggedClose(log, spooler, "spooler")

	for spooler.Spool() {
		event := spooler.Event()
		etype := reflect.TypeOf(event).String()
		hist[etype]++
	}
	if err := spooler.Err(); err != nil {
		return err
	}

	total := 0
	const format = "%d\t%s\n"
	for _, k := range slices.Sorted(maps.Keys(hist)) {
		v := hist[k]
		fmt.Printf(format, v, k)
		total += v
	}
	fmt.Printf(format, total, "total")

	return nil
}
