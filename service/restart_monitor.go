package service

import (
	"context"
	"errors"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	cloudevents "github.com/cloudevents/sdk-go/v2"
	"github.com/google/uuid"

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
}

// Run runs the restart monitor.
func (m *RestartMonitor) Run() {
	if err := m.run(); err != nil {
		m.LogError(err)
	}
}

func (m *RestartMonitor) run() error {
	if m.Condition != ConditionUnset {
		return fmt.Errorf("unexpected initial condition %v", m.Condition)
	}

	if m.EventID == "" {
		eventID, err := uuid.NewRandom()
		if err != nil {
			return err
		}
		m.EventID = eventID.String()
	}

	statedir, err := util.UserStateDir()
	if err != nil {
		log.Println("WARNING:", err)
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
		filenameStem + m.EventID,
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

	m.handleSituation(mtimes[0], mtimes[1], mtimes[2])

	// Rotate the files.
	for i := 1; i < N; i++ {
		oldpath := filenames[i]
		newpath := filenames[i-1]
		err := os.Rename(oldpath, newpath)
		if err == nil || errors.Is(err, os.ErrNotExist) {
			continue
		}
		m.LogWarning(err)
	}

	m.setCondition(ConditionHealthy)
	log.Println("INFO: Service condition:", m.Condition)

	return nil
}

func (m *RestartMonitor) handleSituation(
	startupBeforeLast,
	lastStartup,
	thisStartup time.Time) {

	m.Time = thisStartup

	if lastStartup.IsZero() {
		m.Log("Service started for the first time")
		return
	}

	thisInterval := thisStartup.Sub(lastStartup)
	if thisInterval > RapidRestartCutoff {
		m.Log("Service restarted")
		return
	}

	// At least one rapid restart.
	rapidRestartMessage := fmt.Sprintf(
		"Service restarted after only %.1f seconds",
		thisInterval.Seconds(),
	)

	if startupBeforeLast.IsZero() {
		m.LogWarning(rapidRestartMessage)
		return
	}

	lastInterval := lastStartup.Sub(startupBeforeLast)
	if lastInterval > RapidRestartCutoff {
		m.LogWarning(rapidRestartMessage)
		return
	}

	// At least two rapid restarts in succession.
	m.LogError(rapidRestartMessage)
	m.LogError("Service is restarting rapidly")
	m.coolYourEngines()
}

func (m *RestartMonitor) coolYourEngines() {
	// https://www.youtube.com/watch?v=rsHqcUn6jBY
	log.Println("INFO: Sleeping for", RapidRestartCooldownTime)
	time.Sleep(RapidRestartCooldownTime)
}

// Log logs a informational message.
func (m *RestartMonitor) Log(msg any) {
	m.log("INFO", msg)
}

// LogWarning logs a warning message and marks the service to be in
// dubious condition.
func (m *RestartMonitor) LogWarning(msg any) {
	m.log("WARNING", msg)
	m.setCondition(ConditionDubious)
}

// LogError logs an error message and marks the service to be in an
// error condition.
func (m *RestartMonitor) LogError(msg any) {
	m.log("ERROR", msg)
	m.setCondition(ConditionInError)
}

func (m *RestartMonitor) log(prefix string, msg any) {
	message := fmt.Sprintf("%v", msg)
	log.Println(prefix+":", message)
	m.Messages = append(m.Messages, message)
}

func (m *RestartMonitor) setCondition(c ServiceCondition) {
	if m.Condition < c {
		m.Condition = c
	}
}

// Report publishes a service status report event onto the message bus.
func (m *RestartMonitor) Report(ch *messaging.Channel) {
	event := cloudevents.NewEvent()
	event.SetID(m.EventID)
	event.SetSource(util.ServiceNameURL())
	event.SetType("net.gbenson.hive.service_status_report")
	event.SetTime(m.Time)
	event.SetSubject(util.ServiceName())
	event.SetData(
		cloudevents.ApplicationJSON,
		map[string]any{
			"condition": strings.ToLower(m.Condition.String()),
			"messages":  m.Messages,
		},
	)

	err := ch.PublishEvent(context.Background(), "service.status.reports", event)
	if err != nil {
		log.Println("WARNING:", err)
	}
}
