help:
	@echo 'Use "make setup" to create and populate the database.'

.PHONY: setup

include $(HOME)/.config/hive/mediawiki-mariadb.env
export

# https://www.mediawiki.org/wiki/Topic:Vxp20ag9d6zw5qeo
define REQUIRED_PRIVILEGES =
SELECT,
UPDATE,
INSERT,
DELETE,
ALTER,
CREATE,
INDEX,
DROP,
LOCK TABLES,
USAGE
endef
export REQUIRED_PRIVILEGES

# https://unix.stackexchange.com/a/516476
define _make_grant_privileges_sql =
cat <<EOF | sed -e "/ ON /{s/\"//g}" -e "/^TO /{s/\"/'/g}"
GRANT $REQUIRED_PRIVILEGES ON $MARIADB_DATABASE.*
TO $MARIADB_USER@'%' IDENTIFIED BY $MARIADB_PASSWORD;
EOF
endef
export make_grant_privileges_sql = $(value _make_grant_privileges_sql)

TARGETS = 00-root-password.env 10-grant-privileges.sql 20-import-data.sql.xz


setup: $(addprefix initdb.d/,$(TARGETS))
	docker volume create hive_mediawiki_mariadb > /dev/null
	docker compose run --rm -it mediawiki-mariadb-setup

initdb.d/.gitignore:
	mkdir -p initdb.d || true
	echo '*' > $@

mariadb-root-password.asc:
	(tr </dev/random -dc a-km-z2-8 | head -c20; echo) \
	   | gpg -sear $(shell git config user.email) > $@

initdb.d/00-root-password.env: mariadb-root-password.asc initdb.d/.gitignore
	echo -n 'MARIADB_ROOT_PASSWORD=' > $@
	gpg < $< >> $@

initdb.d/10-grant-privileges.sql: initdb.d/.gitignore; @ eval "$$make_grant_privileges_sql" > $@

initdb.d/20-import-data.sql.xz: initdb.d/.gitignore
	rsync -a hivesite:bak/hivewiki-$(shell date +%Y%m%d).sql.xz $@
