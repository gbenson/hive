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
  && mkdir /usr/lib/hive \
  && ln -s /usr/lib/hive $VIRTUAL_ENV/lib/python*/site-packages \
  && pip install /wheel/*.whl \
  && pip check

RUN ln -s ../../venv/bin/hive-llm-chatbot /usr/bin

RUN set -eux \
  \
  && addgroup --system --gid 471 hive-llm-chatbot \
  && adduser --system --uid 471 --gid 471 \
       --home /var/lib/hive-llm-chatbot --disabled-password hive-llm-chatbot \
  && rm -f /run/adduser \
  && install -d -oroot -ghive-llm-chatbot -m710 /run/secrets

FROM install AS test
RUN set -eux \
  \
  && install -d -ohive-llm-chatbot -ghive-llm-chatbot /src \
  && /venv/bin/pip install \
       pep440-version-utils \
       pytest-cov
COPY tests /src/tests

USER hive-llm-chatbot:hive-llm-chatbot
WORKDIR /src

RUN set -eux \
  \
  && . /venv/bin/activate \
  && pytest --cov hive.llm_chatbot \
  && coverage report > coverage.report

FROM install AS dist
RUN --mount=type=bind,from=test,target=/test \
  grep -q '[^ ][^0]%$' /test/src/coverage.report

USER hive-llm-chatbot:hive-llm-chatbot
WORKDIR /var/lib/hive-llm-chatbot
