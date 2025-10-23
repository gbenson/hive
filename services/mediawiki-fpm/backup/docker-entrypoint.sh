#!/bin/sh
set -eu

# Create a non-root user to work as.
user=mariadb-backup
home=/var/lib/hive/mariadb-backup
uid=729
gid=$uid

addgroup --system --gid $gid $user
adduser --system --uid $uid --gid $gid --home $home --shell /bin/bash --disabled-password $user

# Ensure the volume shared with the backup container is writable.
chown $uid:$gid /var/lib/mysql

# Put MariaDB credentials where mariadb-dump will find them.
. /run/secrets/mediawiki-mariadb.env
chown 0:0 /run/secrets
chmod 700 /run/secrets

rc=$home/.my.cnf
touch $rc
chmod 600 $rc
cat >$rc  <<EOF
[mysqldump]
user=$MARIADB_USER
password=$MARIADB_PASSWORD
EOF
unset MARIADB_USER
unset MARIADB_PASSWORD
chown $uid:$gid $rc

export MARIADB_DATABASE
echo 'info: Dropping privileges ...'
exec su - $user -w MARIADB_DATABASE -c /mariadb-backup.sh
