# Certbot

Certificate management for Hive.

## Usage

Obtain a new certificate:

```sh
docker compose run --rm -it certbot certonly --webroot -w /var/www/letsencrypt -d hive.gbenson.net
```
