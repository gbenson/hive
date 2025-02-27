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

RUN ln -s ../../venv/bin/hive-event-vault /usr/bin

RUN set -eux \
  \
  && addgroup --system --gid 1991 msgstore \
  && adduser --system --uid 1991 --gid 1991 \
       --home /var/lib/hive-event-vault --disabled-password msgstore \
  && rm -f /run/adduser \
  && install -d -oroot -gmsgstore -m710 /run/secrets

FROM install AS test
RUN set -eux \
  \
  && install -d -omsgstore -gmsgstore /src \
  && /venv/bin/pip install \
       pep440-version-utils \
       pytest-cov
COPY tests /src/tests

USER msgstore:msgstore
WORKDIR /src

RUN set -eux \
  \
  && . /venv/bin/activate \
  && pytest --cov hive.event_vault \
  && coverage report > coverage.report

FROM install AS dist
RUN --mount=type=bind,from=test,target=/test \
  grep -q '[^ ][^0]%$' /test/src/coverage.report

RUN set -eux install -d -omsgstore -gmsgstore /data
VOLUME /data
USER msgstore:msgstore
WORKDIR /data

ENTRYPOINT ["hive-event-vault"]
