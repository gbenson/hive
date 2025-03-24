package service

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"time"

	cloudevents "github.com/cloudevents/sdk-go/v2"
	"github.com/google/uuid"
	"github.com/rs/zerolog"

	"gbenson.net/hive/logger"
	"gbenson.net/hive/messaging"
	"gbenson.net/hive/util"
)

const (
	RapidRestartCutoff       = 5 * time.Minute
	RapidRestartCooldownTime = RapidRestartCutoff / 3
)

// A RestartMonitor manages rapid restart mitigation.
type RestartMonitor struct {
	Condition ServiceCondition
	EventID   string
	Time      time.Time
	Messages  []string

	log *logger.Logger
}

// NewRestartMonitor creates a new restart monitor.
func NewRestartMonitor(ctx context.Context) (rsm *RestartMonitor) {
	rsm = &RestartMonitor{
		log: logger.Ctx(ctx),
	}
	if !rsm.IsEnabled() {
		return
	}
	if err := rsm.run(); err != nil {
		rsm.LogError(err)
	}
	return
}

var installedNoMonitorFlag *bool

// IsEnabled reports whether a restart monitor is enabled.
func (rsm *RestartMonitor) IsEnabled() bool {
	if rsm.Condition == ConditionUnmonitored {
		return false
	}

	// Set up -no-monitor, in case Service.Start() uses flag.
	if installedNoMonitorFlag == nil {
		installedNoMonitorFlag = flag.Bool(
			"no-monitor",
			false,
			"run without restart monitoring",
		)
	}

	for _, arg := range os.Args[1:] {
		switch arg {
		case "--no-monitor":
			fallthrough
		case "-no-monitor":
			rsm.Condition = ConditionUnmonitored
			return false
		}
	}

	return true
}

func (rsm *RestartMonitor) run() error {
	eventID, err := uuid.NewRandom()
	if err != nil {
		return err
	}
	rsm.EventID = eventID.String()

	statedir, err := util.UserStateDir()
	if err != nil {
		rsm.LogWarning(err)
		statedir = "/var/lib"
	}
	statedir = filepath.Join(statedir, "hive", util.ServiceName())
	if err := os.MkdirAll(statedir, 0700); err != nil {
		return err
	}
	filenameStem := filepath.Join(statedir, "service-restart.stamp")

	filenames := []string{
		filenameStem + "-",
		filenameStem,
		filenameStem + rsm.EventID,
	}
	N := len(filenames)

	// Touch the new stamp file.
	fp, err := os.Create(filenames[N-1])
	if err != nil {
		return err
	}
	fp.Close()

	// Get all timestamps.
	mtimes := make([]time.Time, N)
	for i, filename := range filenames {
		fi, err := os.Stat(filename)
		if err == nil {
			mtimes[i] = fi.ModTime()
		} else if i == N-1 || !errors.Is(err, os.ErrNotExist) {
			return err
		}
	}

	rsm.handleSituation(mtimes[0], mtimes[1], mtimes[2])

	// Rotate the files.
	for i := 1; i < N; i++ {
		oldpath := filenames[i]
		newpath := filenames[i-1]
		err := os.Rename(oldpath, newpath)
		if err == nil || errors.Is(err, os.ErrNotExist) {
			continue
		}
		rsm.LogWarning(err)
	}

	return nil
}

func (rsm *RestartMonitor) handleSituation(
	startupBeforeLast,
	lastStartup,
	thisStartup time.Time) {

	rsm.Time = thisStartup

	if lastStartup.IsZero() {
		rsm.LogInfo("Service started for the first time")
		return
	}

	thisInterval := thisStartup.Sub(lastStartup)
	if thisInterval > RapidRestartCutoff {
		rsm.LogInfo("Service restarted")
		return
	}

	// At least one rapid restart.
	rapidRestartMessage := fmt.Sprintf(
		"Service restarted after only %.1f seconds",
		thisInterval.Seconds(),
	)

	if startupBeforeLast.IsZero() {
		rsm.LogWarning(rapidRestartMessage)
		return
	}

	lastInterval := lastStartup.Sub(startupBeforeLast)
	if lastInterval > RapidRestartCutoff {
		rsm.LogWarning(rapidRestartMessage)
		return
	}

	// At least two rapid restarts in succession.
	rsm.LogError(rapidRestartMessage)
	rsm.LogError("Service is restarting rapidly")
	rsm.coolYourEngines()
}

func (rsm *RestartMonitor) coolYourEngines() {
	// https://www.youtube.com/watch?v=rsHqcUn6jBY
	rsm.log.Info().
		Str("action", "sleeping").
		Dur("duration", RapidRestartCooldownTime).
		Str("reason", "cooling engines").
		Msg("Restart monitor")
	time.Sleep(RapidRestartCooldownTime)
}

// Log logs a informational message.
func (rsm *RestartMonitor) LogInfo(msg any) {
	rsm.logEvent(rsm.log.Info, msg)
}

// LogWarning logs a warning message and marks the service to be in
// dubious condition.
func (rsm *RestartMonitor) LogWarning(msg any) {
	rsm.logEvent(rsm.log.Warn, msg)
	rsm.setCondition(ConditionDubious)
}

// LogError logs an error message and marks the service to be in an
// error condition.
func (rsm *RestartMonitor) LogError(msg any) {
	rsm.logEvent(rsm.log.Error, msg)
	rsm.setCondition(ConditionInError)
}

func (rsm *RestartMonitor) logEvent(ll func() *zerolog.Event, v any) {
	var msg string

	switch vv := v.(type) {
	case error:
		ll().Err(vv).Msg("Restart monitor")
		msg = vv.Error()
	default:
		msg = fmt.Sprintf("%v", vv)
		ll().Msg(msg)
	}

	rsm.Messages = append(rsm.Messages, msg)
}

func (rsm *RestartMonitor) setCondition(c ServiceCondition) {
	if rsm.Condition < c {
		rsm.Condition = c
	}
}

// Report publishes a service condition report onto the message bus.
func (rsm *RestartMonitor) Report(ctx context.Context, ch *messaging.Channel) {
	event := cloudevents.NewEvent()
	event.SetID(rsm.EventID)
	event.SetSource(util.ServiceNameURL())
	event.SetType("net.gbenson.hive.service_status_report")
	event.SetTime(rsm.Time)
	event.SetSubject(util.ServiceName())
	event.SetData(
		cloudevents.ApplicationJSON,
		map[string]any{
			"condition": rsm.Condition.String(),
			"messages":  rsm.Messages,
		},
	)

	err := ch.PublishEvent(context.Background(), "service.status.reports", event)
	if err != nil {
		logger.Ctx(ctx).Warn().Err(err).Msg("Restart monitor")
		return
	}
}
