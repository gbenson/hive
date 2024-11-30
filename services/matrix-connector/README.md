[![version badge]](https://hub.docker.com/r/gbenson/hive-matrix-connector)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-matrix-connector?color=limegreen

# hive-matrix-connector

Matrix connector service for Hive.

## Set up development environment

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/matrix-connector
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```

## Create sessions

### In development environment

```sh
matrix-commander --login password
# ...follow prompts...
mkdir -p -m700 ~/.{config,local/share}/matrix-commander
mv credentials.json ~/.config/matrix-commander
mv store ~/.local/share/matrix-commander
matrix-commander --verify
# ...follow prompts, then Ctrl-C when you see "got verification mac"
matrix-commander -m 'hello world!'
```

### In production container

```sh
docker-compose exec matrix-sender bash
chmod o-rwx .
/venv/bin/matrix-commander --login password
# ...follow prompts...
/venv/bin/matrix-commander --verify
# ...follow prompts, then Ctrl-C when you see "got verification mac"
exit  # ...then repeat for receiver
```
