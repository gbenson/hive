[![version badge]](https://hub.docker.com/r/gbenson/hive-service-monitor)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-service-monitor?color=limegreen

# hive-service-monitor

Service status monitor for Hive

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/service-monitor
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
