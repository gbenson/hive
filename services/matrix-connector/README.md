[![version badge]](https://hub.docker.com/r/gbenson/hive-matrix-connector)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-matrix-connector?color=limegreen

# hive-matrix-connector

Matrix connector service for Hive.

## Setup

### Development

```sh
pip install -e .
matrix-commander --login password
# ...follow prompts...
mkdir -p -m700 ~/.{config,local/share}/matrix-commander
mv credentials.json ~/.config/matrix-commander
mv store ~/.local/share/matrix-commander
matrix-commander --verify
# ...follow prompts, then Ctrl-C when you see "got verification mac"
matrix-commander -m 'hello world!'
```

### Production

```sh
docker-compose exec matrix-sender bash
chmod o-rwx .
/venv/bin/matrix-commander --login password
# ...follow prompts...
/venv/bin/matrix-commander --verify
# ...follow prompts, then Ctrl-C when you see "got verification mac"
exit  # ...then repeat for receiver
```
