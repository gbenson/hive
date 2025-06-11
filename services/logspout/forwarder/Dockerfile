FROM golang:bookworm AS builder
ARG SERVICE=log-forwarder
WORKDIR /go/src
COPY go.mod go.sum ./
RUN go mod edit -droprequire maunium.net/go/mautrix
RUN go mod download
COPY . ./
RUN rm -rf services/matrix-connector
RUN go mod tidy
ENV CGO_ENABLED=0
RUN ci/go-vet
RUN go build -trimpath -ldflags="-s -w" ./services/logspout/forwarder/cmd/hive-$SERVICE.go
RUN mkdir empty

FROM scratch
ARG SERVICE=log-forwarder
ARG UID=588
ARG GID=$UID

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=builder --chown=0:0 --chmod=755 /go/src/hive-$SERVICE /
COPY --from=builder --chown=0:$GID --chmod=710 /go/src/empty /run/secrets

USER $UID:$GID
ENTRYPOINT ["/hive-log-forwarder"]
