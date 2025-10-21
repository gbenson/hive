ARG BASE_IMAGE=debian:13-slim

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
       borgbackup \
       ssh \
  && rm -f /var/lib/dpkg/*-old

COPY --chmod=755 docker-entrypoint.sh /
COPY --chmod=644 hive-borg-activate.sh /usr/bin/hive-borg-activate

ENTRYPOINT ["/docker-entrypoint.sh"]
