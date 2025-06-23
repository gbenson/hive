[![version badge]](https://hub.docker.com/r/gbenson/hive-log-collector)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-log-collector?color=limegreen

# hive-log-collector

Log collector service for Hive.

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
gofmt -w . && ./ci/go-vet && ./ci/go-test && \
LL=debug go run ./services/logging/collector/cmd/hive-log-collector.go
```
