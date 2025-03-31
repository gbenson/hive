ARG BASE_IMAGE=debian:12-slim

FROM ${BASE_IMAGE} AS base
ENV DEBIAN_FRONTEND=noninteractive

RUN --mount=type=tmpfs,target=/var/cache \
    --mount=type=tmpfs,target=/var/lib/apt/lists \
    --mount=type=tmpfs,target=/var/log \
  set -eux \
  \
  && apt-get -y update \
  && apt-get -y upgrade --no-install-recommends \
  && apt-get -y install --no-install-recommends \
       python3 \
       python3-venv \
       libmagic1 \
       libolm3 \
  && rm -f /var/lib/dpkg/*-old

RUN --mount=type=tmpfs,target=/root/.cache \
  set -eux \
  \
  && python3 -m venv /venv \
  && . /venv/bin/activate \
  && pip install --upgrade pip \
  && pip install wheel

FROM base AS wheel
RUN mkdir -p /src
COPY services/matrix-connector/hive /src/hive
COPY services/matrix-connector/pyproject.toml /src
COPY services/matrix-connector/README.md /src
RUN /venv/bin/pip wheel --no-deps /src

FROM golang:bookworm AS builder
ARG SERVICE=matrix-connector
RUN apt-get -y update
RUN apt-get -y install --no-install-recommends libolm-dev

WORKDIR /go/src
COPY go.mod go.sum ./
RUN go mod download
COPY . ./
RUN gofmt -w .
RUN ci/go-vet
RUN ci/go-test
RUN go build -trimpath -ldflags="-s -w" ./services/$SERVICE/cmd/hive-$SERVICE.go

FROM base AS install
RUN --mount=type=bind,from=wheel,target=/wheel \
    --mount=type=tmpfs,target=/root/.cache \
  set -eux \
  \
  && python3 -m venv /venv \
  && . /venv/bin/activate \
  && pip install /wheel/*.whl \
  && pip check

RUN set -eux \
  \
  && ln -s ../../venv/bin/matrix-commander /usr/bin \
  && ln -s ../../venv/bin/hive-matrix-sender /usr/bin \
  && ln -s ../../venv/bin/hive-matrix-receiver /usr/bin \
  && ln -s ../../venv/bin/hive-matrix-transitioner /usr/bin

RUN set -eux \
  \
  && addgroup --system --gid 6617 hivetrix \
  && adduser --system --uid 6617 --gid 6617 \
       --home /var/lib/hive/matrix-connector --disabled-password hivetrix \
  && rm -f /run/adduser \
  && install -d -oroot -ghivetrix -m710 /run/secrets

FROM install AS test
RUN set -eux \
  \
  && install -d -ohivetrix -ghivetrix /src \
  && /venv/bin/pip install \
       pep440-version-utils \
       pytest-cov
COPY services/matrix-connector/tests /src/tests

USER hivetrix:hivetrix
WORKDIR /src

RUN set -eux \
  \
  && . /venv/bin/activate \
  && pytest --cov hive.matrix_connector \
  && coverage report > coverage.report

FROM install AS dist
ARG SERVICE=matrix-connector
RUN --mount=type=bind,from=test,target=/test \
  grep -q '[^ ][^0]%$' /test/src/coverage.report
COPY --from=builder --chown=0:0 --chmod=755 /go/src/hive-$SERVICE /usr/bin

USER hivetrix:hivetrix
WORKDIR /var/lib/hive/matrix-connector
