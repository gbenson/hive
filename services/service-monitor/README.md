[![version badge]](https://hub.docker.com/r/gbenson/hive-service-monitor)
[![documentation badge]](https://pkg.go.dev/gbenson.net/hive/services/service-monitor)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-service-monitor?color=limegreen
[documentation badge]: https://pkg.go.dev/badge/gbenson.net/hive/services/service-monitor.svg

# hive-service-monitor

Service status monitor for Hive

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive
gofmt -w . && LL=debug go run ./services/service-monitor/cmd/hive-service-monitor.go
```
