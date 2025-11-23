FROM mediawiki:1.43.5-fpm

# https://www.mediawiki.org/wiki/Special:ExtensionDistributor?extdistname=Scribunto&extdistversion=REL1_43
ARG MOBILE_FRONTEND=extensions/MobileFrontend-REL1_43-148ff5d.tar.gz
ARG SCRIBUNTO=extensions/Scribunto-REL1_43-74f7d10.tar.gz
ARG TEMPLATE_STYLES=extensions/TemplateStyles-REL1_43-adea53c.tar.gz

# File ownership and permissions under /var/www/html are a mess!
# The obvious solution is:
# ```
# RUN set -eu \
#   && chmod -t . \
#   && chown -R 0:0 . \
#   && chmod -R og-w . \
#   && chown www-data:www-data cache
# ```
# ...except there's nearly 24,000 files and directories in there,
# and doing that adds over 200 MiB to the container image (from
# 788 MiB to 994 MiB!)  I hate not blanket-fixing everything, but
# the RUN instruction below changes only what's necessary to stop
# PHP-FPM being able to write where it shouldn't, and "only" adds
# 60 MiB to the image :(
RUN set -eu \
  && chmod og-wt . \
  && find \( -user www-data -or -group www-data \) -not -name cache -print0 | xargs -0 chown 0:0

RUN --mount=type=bind,source=${MOBILE_FRONTEND},target=/tmp/MobileFrontend.tar.gz \
  set -eux \
  && tar -C extensions -xzf /tmp/MobileFrontend.tar.gz \
  && chmod -R og-w extensions/MobileFrontend \
  && chown -R 0:0 extensions/MobileFrontend \
  && find -name '.git*' -print0 | xargs -0 rm -f

RUN --mount=type=bind,source=${SCRIBUNTO},target=/tmp/Scribunto.tar.gz \
  set -eux \
  && tar -C extensions -xzf /tmp/Scribunto.tar.gz \
  && chmod -R og-w extensions/Scribunto \
  && chown -R 0:0 extensions/Scribunto \
  && find -name '.git*' -print0 | xargs -0 rm -f

RUN --mount=type=bind,source=${TEMPLATE_STYLES},target=/tmp/TemplateStyles.tar.gz \
  set -eux \
  && tar -C extensions -xzf /tmp/TemplateStyles.tar.gz \
  && chmod -R og-w extensions/TemplateStyles \
  && chown -R 0:0 extensions/TemplateStyles \
  && find -name '.git*' -print0 | xargs -0 rm -f
