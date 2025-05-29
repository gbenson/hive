#!/bin/sh
set -eu

chown 0:0 /run/secrets
chmod 700 /run/secrets

install -m400 /run/secrets/ssh_host_*_key /etc/ssh

install -d -m700 /run/sshd /root/.ssh
cat /run/secrets/authorized_keys | while read -r key; do
  echo "command=\"rsync --server --sender -logDtpre.iLsfxCIvu . /srv/\" $key" >> /root/.ssh/authorized_keys
done
chmod 400 /root/.ssh/authorized_keys

exec /usr/sbin/sshd -D -e "$@"
