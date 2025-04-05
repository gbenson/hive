[![version badge]](https://hub.docker.com/r/gbenson/hive-event-vault)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-event-vault?color=limegreen

# hive-event-vault

Event vault for Hive

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/event-vault
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
