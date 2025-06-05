#!/bin/bash
set -euo pipefail

chown 0:0 /run/secrets
chmod 700 /run/secrets

DAILY_RSYNC_TIME='5:15am'

. /run/secrets/certdist-server.env

install -d -m700 /root/.ssh
echo "$CERTDIST_HOST $CERTDIST_HOST_KEY" > /root/.ssh/known_hosts
chmod 400 /root/.ssh/known_hosts

ssh-keygen -A

unixtime() {
  date +%s -d "$@"
}

sshcmd="ssh -p '$CERTDIST_PORT' -i /run/secrets/id_ed25519"
target="/srv"
source="$CERTDIST_HOST:$target/"

echo 'info: Doing initial sync'
while true; do
  rsync -av --delete -e "$sshcmd" "$source" "$target"

  next_rsync_time=$(unixtime "$DAILY_RSYNC_TIME")
  seconds_to_sleep=$((next_rsync_time - $(unixtime now)))
  if ((seconds_to_sleep < 300)); then
      next_rsync_time=$(unixtime "$DAILY_RSYNC_TIME tomorrow")
      seconds_to_sleep=$((next_rsync_time - $(unixtime now)))
  fi

  echo "info: Sleeping until $(date -d @$next_rsync_time) ..."
  sleep $((seconds_to_sleep + 1))
done
