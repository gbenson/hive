#!/bin/bash
set -euo pipefail

echo "info: Now $(id)"
umask 022

DAILY_BACKUP_TIME='4am'
WRITE_BACKUPS_TO='/var/lib/mysql'

unixtime() {
  date +%s -d "$@"
}

backup_filename() {
  date "+$WRITE_BACKUPS_TO/%Y/%m/mw-mariadb-%Y%m%d.sql.xz" "$@"
}

backup_exists() {
  [ -s "$@" ] || return 1
  xz -l "$@" | grep -q ' 0 ' && return 1
  return 0
}

next_backup_time=$(unixtime "$DAILY_BACKUP_TIME")
while true; do
  next_backup_file=$(backup_filename -d @$next_backup_time)

  # If today's snapshot exists then move on to tomorrow.
  if backup_exists "$next_backup_file"; then
    next_backup_time=$(unixtime "$DAILY_BACKUP_TIME tomorrow")

    next_backup_file=$(backup_filename -d @$next_backup_time)
    if [ -f "$next_backup_file" ]; then
      echo "error: Tomorrow's $next_backup_file already exists?!"
      exit 1
    fi
  fi

  # Sleep until it's time to write the next snapshot.
  seconds_to_sleep=$((next_backup_time - $(unixtime now)))
  if ((seconds_to_sleep > 0)); then
    echo "info: Sleeping until $(date -d @$next_backup_time) ..."
    sleep $((seconds_to_sleep + 1))
    continue
  fi

  # mariadb-dump is much faster than xz (around 5 seconds vs over
  # a minute) so we snapshot in two steps to keep the snapshot as
  # close to an instant in time as possible.  This isn't perfect,
  # but it is good enough.
  next_backup_file=$(echo "$next_backup_file" | sed 's/\.xz$//')
  if [ -f "$next_backup_file" ]; then
    echo "warning: $next_backup_file will be overwritten!"
  fi

  echo "info: Writing $next_backup_file ..."
  mkdir -p $(dirname "$next_backup_file")
  mariadb-dump \
    --host=mediawiki-mariadb \
    --no-tablespaces \
    "$MARIADB_DATABASE" > "$next_backup_file"

  if [ ! -s "$next_backup_file" ]; then
    echo "error: $next_backup_file not written!"
    exit 1
  fi

  echo "info: Compressing ..."
  xz "$next_backup_file"
  next_backup_file="$next_backup_file.xz"

  xz -l "$next_backup_file" | while read -r line; do
    echo "info: $line"
  done

  if xz -t "$next_backup_file"; then
    echo "info: Snapshot looks good"
  else
    echo "error: $next_backup_file not ok?!"
    exit 1
  fi
done
