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
       libolm3 \
  && rm -f /var/lib/dpkg/*-old

FROM golang:bookworm AS builder
ARG SERVICE=matrix-connector
RUN apt-get -y update
RUN apt-get -y install --no-install-recommends libolm-dev

WORKDIR /go/src
COPY go.mod go.sum ./
RUN go mod edit -droprequire github.com/coreos/go-systemd/v22
RUN go mod download
COPY . ./
RUN rm -rf services/logging/collector
RUN gofmt -w .
RUN ci/go-vet
RUN ci/go-test
RUN go build -trimpath -ldflags="-s -w" ./services/$SERVICE/cmd/hive-$SERVICE.go

FROM base AS install
RUN set -eux \
  \
  && addgroup --system --gid 6617 hivetrix \
  && adduser --system --uid 6617 --gid 6617 \
       --home /var/lib/hive/matrix-connector --disabled-password hivetrix \
  && rm -f /run/adduser \
  && install -d -oroot -ghivetrix -m710 /run/secrets

FROM install AS dist
ARG SERVICE=matrix-connector
COPY --from=builder --chown=0:0 --chmod=755 /go/src/hive-$SERVICE /usr/bin

USER hivetrix:hivetrix
WORKDIR /var/lib/hive/matrix-connector
ENTRYPOINT ["hive-matrix-connector"]
