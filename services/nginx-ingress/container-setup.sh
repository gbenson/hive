#!/bin/sh
chown 0:0 /run/secrets
chmod 700 /run/secrets
cat /run/secrets/mediawiki.htpasswd > /etc/nginx/mediawiki.htpasswd
