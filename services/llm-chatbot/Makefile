all: build

.PHONY: build check lint test venv

check: test

VENV ?= .venv
PIP ?= $(VENV)/bin/pip

$(VENV):
	python3 -m venv $@

venv: $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

lint:
	flake8
	mypy --explicit-package-bases hive

test: lint
	pytest
