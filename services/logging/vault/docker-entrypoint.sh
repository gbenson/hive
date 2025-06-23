#!/bin/sh
set -e

chown 0:mongodb /run/secrets
chmod 710 /run/secrets

exec docker-entrypoint.sh "$@"
