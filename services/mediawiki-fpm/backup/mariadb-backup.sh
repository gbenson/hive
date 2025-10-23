#!/bin/bash
set -euo pipefail

echo "info: Now $(id)"
umask 022

DAILY_BACKUP_TIME='4am'
SNAPSHOT_FILENAME='/var/lib/mysql/snapshot.sql'
SNAPSHOT_TEMPFILE="${SNAPSHOT_FILENAME}.tmp"

unixtime() {
  date +%s -d "$@"
}

while true; do
  next_backup_time=$(unixtime "$DAILY_BACKUP_TIME")
  seconds_to_sleep=$((next_backup_time - $(unixtime now)))
  if ((seconds_to_sleep < 300)); then
      next_backup_time=$(unixtime "$DAILY_BACKUP_TIME tomorrow")
      seconds_to_sleep=$((next_backup_time - $(unixtime now)))
  fi

  echo "info: Sleeping until $(date -d @$next_backup_time) ..."
  sleep $((seconds_to_sleep + 1))

  echo "info: Updating ${SNAPSHOT_FILENAME} ..."
  mariadb-dump \
    --host=mediawiki-mariadb \
    --no-tablespaces \
    "$MARIADB_DATABASE" > "$SNAPSHOT_TEMPFILE"
  mv -f "$SNAPSHOT_TEMPFILE" "${SNAPSHOT_FILENAME}"
  echo "info: ${SNAPSHOT_FILENAME} updated"
done
