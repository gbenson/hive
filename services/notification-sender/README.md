[![version badge]](https://hub.docker.com/r/gbenson/hive-notification-sender)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-notification-sender?color=limegreen

# hive-notification-sender

Notification sender for Hive

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/notification-sender
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
