FROM mediawiki:1.35.10-fpm

ARG MOBILE_FRONTEND=extensions/MobileFrontend-REL1_35-1421405.tar.gz
ARG SCRIBUNTO=extensions/Scribunto-REL1_35-d21b655.tar.gz
ARG TEMPLATE_STYLES=extensions/TemplateStyles-REL1_35-7a40a6a.tar.gz
ARG MINERVA_NEUE=skins/MinervaNeue-REL1_35-d82e32c.tar.gz

RUN --mount=type=bind,source=${MOBILE_FRONTEND},target=/tmp/MobileFrontend.tar.gz \
  set -eux \
  && tar -C extensions -xzf /tmp/MobileFrontend.tar.gz \
  && find -name '.git*' -print0 | xargs -0 rm -f

RUN --mount=type=bind,source=${SCRIBUNTO},target=/tmp/Scribunto.tar.gz \
  set -eux \
  && tar -C extensions -xzf /tmp/Scribunto.tar.gz \
  && find -name '.git*' -print0 | xargs -0 rm -f

RUN --mount=type=bind,source=${TEMPLATE_STYLES},target=/tmp/TemplateStyles.tar.gz \
  set -eux \
  && tar -C extensions -xzf /tmp/TemplateStyles.tar.gz \
  && find -name '.git*' -print0 | xargs -0 rm -f

RUN --mount=type=bind,source=${MINERVA_NEUE},target=/tmp/MinervaNeue.tar.gz \
  set -eux \
  && tar -C extensions -xzf /tmp/MinervaNeue.tar.gz \
  && find -name '.git*' -print0 | xargs -0 rm -f
