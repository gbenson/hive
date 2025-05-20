[![version badge]](https://hub.docker.com/r/gbenson/mediawiki-fpm)

[version badge]: https://img.shields.io/docker/v/gbenson/mediawiki-fpm?color=limegreen

# hive-mediawiki-fpm

PHP-FPM MediaWiki for Hive

## Database setup

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/mediawiki-fpm
make setup
```

Note that `make setup` never exits, you'll have to `docker stop` the
container it starts from another terminal.


## Testing

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/mediawiki-fpm
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
flake8 && pytest --log-level=INFO
```
