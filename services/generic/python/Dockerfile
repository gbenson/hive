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
  && rm -f /var/lib/dpkg/*-old

RUN --mount=type=tmpfs,target=/root/.cache \
  set -eux \
  \
  && python3 -m venv /venv \
  && . /venv/bin/activate \
  && pip install --upgrade pip \
  && pip check

FROM scratch AS src
COPY requirements.txt /

FROM base
RUN --mount=type=bind,from=src,target=/src \
    --mount=type=tmpfs,target=/root/.cache \
  set -eux \
  \
  && python3 -m venv /venv \
  && . /venv/bin/activate \
  && pip install -r /src/requirements.txt \
  && pip check

RUN set -eux \
  \
  && addgroup --system --gid 6130 hive \
  && adduser --system --uid 6130 --gid 6130 \
       --home /var/lib/hive/service --disabled-password hive \
  && rm -f /run/adduser \
  && install -d -oroot -ghive -m710 /run/secrets

USER hive:hive
WORKDIR /
