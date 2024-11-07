[![version badge]](https://hub.docker.com/r/gbenson/hive-vane-webui-api)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-vane-webui-api?color=limegreen

# hive-vane-webui-api

Web chat API gateway for Hive

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/vane-webui-api
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .[dev]
flake8 && pytest
```
