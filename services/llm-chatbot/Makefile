all: build

.PHONY: build check lint test

check: test

lint:
	flake8

test: lint
	pytest
