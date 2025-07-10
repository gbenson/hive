#!/bin/sh
chown 0:0 /run/secrets
chmod 700 /run/secrets
for f in /run/secrets/*.htpasswd; do
  cat $f > /etc/nginx/$(basename $f)
done
