. /run/secrets/backup-server.env

export BORG_REPO="${HIVE_BORG_REPO_PREFIX}${HIVE_BORG_REPO}"
export BORG_PASSCOMMAND='cat /run/secrets/backup-passphrase'

configure_ssh=1
for f in /root/.ssh/id_* /root/.ssh/known_hosts; do
  [ -e "$f" ] || continue
  configure_ssh=0
done
unset f

if [ "$configure_ssh" = 1 ]; then
  install -d -m700 /root/.ssh
  install -m400 /run/secrets/id_* /root/.ssh
  echo "${HIVE_BORG_SSH_KNOWN_HOSTS}" > /root/.ssh/known_hosts
  chmod 400 /root/.ssh/known_hosts
fi
unset configure_ssh
