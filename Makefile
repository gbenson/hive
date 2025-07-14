all: build

.PHONY: build check lint test

check: test

lint:
	gofmt -w .
	go vet ./...

test: lint
	go test -coverprofile=coverage.out ./...

coverage.html: coverage.out
	go tool cover -html=$< -o $@
