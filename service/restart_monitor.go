package service

import (
	"log"

	"gbenson.net/hive/messaging"
)

type RestartMonitor struct {
	ReportSent bool
}

func (rsm *RestartMonitor) Run() {
	log.Println("WARNING: ReportMonitor.Run: Not implemented")
}

func (rsm *RestartMonitor) Report(ch *messaging.Channel) {
	if rsm.ReportSent {
		return
	}

	log.Println("WARNING: ReportMonitor.Report: Not implemented")

	rsm.ReportSent = true
}
