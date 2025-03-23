[![version badge]](https://hub.docker.com/r/gbenson/hive-transitioner)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-transitioner?color=limegreen

# hive-transitioner

Transition manager for Hive 🏳️‍⚧️

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/events/transitioner
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
