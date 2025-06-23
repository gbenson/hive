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
       ca-certificates \
  && rm -f /var/lib/dpkg/*-old

FROM golang:bookworm AS builder
ARG SERVICE=log-ingester
WORKDIR /go/src
COPY go.mod go.sum ./
RUN go mod edit -droprequire maunium.net/go/mautrix
RUN go mod edit -droprequire github.com/coreos/go-systemd/v22
RUN go mod download
COPY . ./
RUN rm -rf services/matrix-connector services/logging/collector
RUN gofmt -w .
RUN ci/go-vet
RUN ci/go-test
RUN go build -trimpath -ldflags="-s -w" \
    ./services/logging/ingester/cmd/hive-$SERVICE.go

FROM base AS install
RUN set -eux \
  \
  && install -d -m700 /run/secrets

FROM install AS dist
ARG SERVICE=log-ingester
COPY --from=builder --chown=0:0 --chmod=755 /go/src/hive-$SERVICE /usr/bin

ENTRYPOINT ["hive-log-ingester"]
