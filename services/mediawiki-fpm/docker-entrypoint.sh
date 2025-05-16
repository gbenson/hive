#!/bin/sh

set -e

make_script() {
  echo 'set -e'

  find /run/secrets/ -follow -type f -name '*.env' -print \
    | sort -V \
    | while read -r f; do
        echo ". \"$f\""
  done

  echo "sed \\"
  for v in \
    mariadb_database \
    mariadb_password \
    mariadb_user \
    service_hostname \
    wg_article_path \
    wg_resource_base_path \
    wg_script_path \
    wg_secret_key \
    wg_upgrade_key \
    wg_upload_path \
  ; do
    u=$(echo $v | tr a-z A-Z)
    echo "  -e \"s/{{[[:space:]]*$v[[:space:]]*}}/\$$u/g\" \\"
  done
  echo '/etc/mediawiki/LocalSettings.php.template > LocalSettings.php'
}

script=$(mktemp)
make_script >> "$script"
sh "$script"
rm -f "$script"

exec docker-php-entrypoint "$@"
