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
COPY hive /src/hive
COPY pyproject.toml README.md /src
RUN /venv/bin/pip wheel --no-deps /src

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
  && ln -s ../../venv/bin/hive-matrix-receiver /usr/bin

RUN set -eux \
  \
  && addgroup --system --gid 6617 hivetrix \
  && adduser --system --uid 6617 --gid 6617 \
       --home /var/lib/matrix --disabled-password hivetrix \
  && rm -f /run/adduser \
  && install -d -oroot -ghivetrix -m710 /run/secrets

USER hivetrix:hivetrix
WORKDIR /var/lib/matrix
