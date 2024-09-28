[![version badge]](https://hub.docker.com/r/gbenson/hive-reading-list-updater)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-reading-list-updater?color=limegreen

# hive-reading-list-updater

Reading list updater for Hive

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/reading-list-updater
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8
```
