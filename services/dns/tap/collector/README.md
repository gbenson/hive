[![version badge]](https://hub.docker.com/r/gbenson/hive-dnstap-collector)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-dnstap-collector?color=limegreen

# hive-dnstap-collector

dnstap collector service for Hive.

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
make check && \
LL=debug go run ./services/dns/tap/collector/cmd/hive-dnstap-collector.go
```
