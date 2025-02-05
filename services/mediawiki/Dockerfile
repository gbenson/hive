FROM mediawiki:1.35.10

ARG GITHUB_SERVER_URL=https://github.com
ARG GITHUB_REPOSITORY=gbenson/hivesite
ARG GITHUB_SHA=72daf16765d4dc5aedab0c51a95fbaf973f8191f

ARG repo_url=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}
ARG image_source_url=${repo_url}/blob/${GITHUB_SHA}/source

RUN set -eux; \
# Extensions
  for i in \
    MobileFrontend-REL1_35-1421405.tar.gz \
    Scribunto-REL1_35-d21b655.tar.gz \
    TemplateStyles-REL1_35-7a40a6a.tar.gz \
  ;do \
    curl -fSL ${image_source_url}/$i?raw=true \
      | tar -C extensions -xz \
  ;done; \
# Skins
  for i in \
    MinervaNeue-REL1_35-d82e32c.tar.gz \
  ;do \
    curl -fSL ${image_source_url}/$i?raw=true \
      | tar -C skins -xz \
  ;done; \
# Remove any .gitignore etc files that got dropped in
  find -name '.git*' -print0 | xargs -0 rm -f
