[![version badge]](https://hub.docker.com/r/gbenson/hive-matrix-connector)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-matrix-connector?color=limegreen

# hive-matrix-connector

Matrix connector service for Hive.

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
make check && \
LL=debug go run ./services/matrix-connector/cmd/hive-matrix-connector.go
```
