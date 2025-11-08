[![version badge]](https://hub.docker.com/r/gbenson/hive-dnstap-integrator)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-dnstap-integrator?color=limegreen

# hive-dnstap-integrator

dnstap integrator service for Hive.

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
make check && \
LL=debug go run ./services/dns/tap/integrator/cmd/hive-dnstap-integrator.go
```
