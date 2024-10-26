[![version badge]](https://hub.docker.com/r/gbenson/hive-matrix-router)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-matrix-router?color=limegreen

# hive-matrix-router

Incoming Matrix event router for Hive

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/matrix-router
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
