FROM golang:bookworm AS builder
ARG SERVICE=service-monitor
WORKDIR /go/src
COPY go.mod go.sum ./
RUN go mod edit -droprequire maunium.net/go/mautrix
RUN go mod download
COPY . ./
RUN rm -rf matrix cmd/hive-matrix-connector
RUN go mod tidy
ENV CGO_ENABLED=0
RUN ci/go-vet
RUN go build -trimpath -ldflags="-s -w" ./services/$SERVICE/cmd/hive-$SERVICE.go
RUN mkdir empty

FROM scratch
ARG SERVICE=service-monitor
ARG UID=2896
ARG GID=$UID
ENV XDG_STATE_HOME=/var/lib

COPY --from=builder --chown=0:0 --chmod=755 /go/src/hive-$SERVICE /
COPY --from=builder --chown=0:$GID --chmod=710 /go/src/empty /run/secrets
COPY --from=builder --chown=$UID:$GID --chmod=700 /go/src/empty $XDG_STATE_HOME/hive

VOLUME $XDG_STATE_HOME/hive
USER $UID:$GID
ENTRYPOINT ["/hive-service-monitor"]
