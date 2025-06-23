[![version badge]](https://hub.docker.com/r/gbenson/hive-log-ingester)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-log-ingester?color=limegreen

# hive-log-ingester

Log ingester service for Hive.

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
gofmt -w . && ./ci/go-vet && ./ci/go-test && \
LL=debug go run ./services/logging/ingester/cmd/hive-log-ingester.go
```
