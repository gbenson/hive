FROM golang:bookworm AS builder
ARG SERVICE=log-ingester
ENV CGO_ENABLED=0
WORKDIR /go/src
COPY go.mod go.sum ./
RUN go mod edit -droprequire maunium.net/go/mautrix
RUN go mod edit -droprequire github.com/coreos/go-systemd/v22
RUN go mod download
COPY . ./
RUN rm -rf services/matrix-connector services/logging/collector
RUN go mod tidy
RUN make check
RUN go build -trimpath -ldflags="-s -w" \
    ./services/logging/ingester/cmd/hive-$SERVICE.go
RUN mkdir empty

FROM gcr.io/distroless/static
ARG SERVICE=log-ingester
ARG UID=389
ARG GID=$UID

COPY --from=builder --chown=0:0 --chmod=755 /go/src/hive-$SERVICE /
COPY --from=builder --chown=0:$GID --chmod=710 /go/src/empty /run/secrets

USER $UID:$GID
ENTRYPOINT ["/hive-log-ingester"]
