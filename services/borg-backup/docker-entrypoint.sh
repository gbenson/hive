#!/bin/bash
set -euo pipefail

chown 0:0 /run/secrets
chmod 700 /run/secrets

. /usr/bin/hive-borg-activate

cd "/srv/$HIVE_BORG_REPO"

DAILY_BACKUP_TIME=${HIVE_DAILY_BACKUP_TIME:-'5:05am'}

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

  "$@" 2>&1
done
