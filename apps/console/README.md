# hive-console

Live view of Hive's system logs.

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
gofmt -w . && ./ci/go-vet && ./ci/go-test && go run ./apps/console/cmd/hive-console.go
```
