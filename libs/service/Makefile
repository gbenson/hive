all: build

.PHONY: build check lint test

check: test

lint:
	flake8
	mypy --explicit-package-bases hive

test: lint
	pytest
