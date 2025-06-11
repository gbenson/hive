[![version badge]](https://hub.docker.com/r/gbenson/hive-log-forwarder)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-log-forwarder?color=limegreen

# hive-log-forwarder

Log forwarder service for Hive.

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
gofmt -w . && ./ci/go-vet && ./ci/go-test && \
LL=debug go run ./services/logspout/forwarder/cmd/hive-log-forwarder.go
```
