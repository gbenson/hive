[![version badge]](https://hub.docker.com/r/gbenson/hive-log-spooler)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-log-spooler?color=limegreen

# hive-log-spooler

Log spooler service for Hive.

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
gofmt -w . && ./ci/go-vet && ./ci/go-test && \
LL=debug go run ./services/logging/spooler/cmd/hive-log-spooler.go
```
