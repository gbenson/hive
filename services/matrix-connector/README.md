[![version badge]](https://hub.docker.com/r/gbenson/hive-matrix-connector)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-matrix-connector?color=limegreen

# hive-matrix-connector

Matrix connector service for Hive.

## Setup

```sh
pip install -e .
matrix-commander --login password
mkdir -p -m700 ~/{.config,local/share}/matrix-commander
mv credentials.json ~/.config/matrix-commander
mv store ~/.local/share/matrix-commander
matrix-commander --verify
matrix-commander -m 'hello world!'
```
