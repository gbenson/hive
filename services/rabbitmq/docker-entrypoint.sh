#!/bin/sh

set -e
chown 0:0 /run/secrets
chmod 700 /run/secrets

chmod -R og-wt /etc/rabbitmq 2>/dev/null || true
chown -R 0:0   /etc/rabbitmq 2>/dev/null || true

# Install the certs
src=/etc/letsencrypt/live/$HOSTNAME
dst=/etc/rabbitmq/certs

install -d -g rabbitmq -m750 $dst

install -g rabbitmq -m644 $src/chain.pem $dst/ca_certificate.pem
install -g rabbitmq -m644 $src/cert.pem $dst/server_certificate.pem
install -g rabbitmq -m640 $src/privkey.pem $dst/server_key.pem

unset src dst

# Install rabbitmq.conf
make_script() {
  echo 'set -e'
  echo 'cd /etc/rabbitmq/conf.d'

  find /run/secrets/ -follow -type f -name '*.env' -print \
    | sort -V \
    | while read -r f; do
        echo ". \"$f\""
  done

  echo "sed \\"
  for v in \
    rabbitmq_default_user \
    rabbitmq_default_pass \
  ; do
    u=$(echo $v | tr a-z A-Z)
    echo "  -e \"s/{{[[:space:]]*$v[[:space:]]*}}/\$$u/g\" \\"
  done
  file='20-hive.conf'
  echo "$file.template > $file"
  echo "chmod 640 $file"
  echo "chgrp rabbitmq $file"
}

script=$(mktemp)
make_script >> "$script"
sh "$script"
rm -f "$script"

exec rabbitmq-server "$@"
