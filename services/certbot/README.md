# Certbot

Certificate management for Hive.

## Usage

Obtain a new certificate:

```sh
docker compose run --rm -it certbot certonly --webroot -w /var/www/letsencrypt -d hive.gbenson.net
```

Setup auto-renew:

Add this to your crontab:

```
0 4 * * *  /path/to/hive/services/certbot/auto-renew.cron
```
