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
       openssh-server \
       rsync \
  && rm -f /etc/ssh/ssh_host_*_key* \
  && rm -f /var/lib/dpkg/*-old

COPY --chmod=755 docker-entrypoint.sh /
COPY --chmod=600 sshd_config /etc/ssh/sshd_config.d/hive-rsync.conf

ENTRYPOINT ["/docker-entrypoint.sh"]
