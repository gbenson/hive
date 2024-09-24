[![version badge]](https://hub.docker.com/r/gbenson/hive-email-receiver)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-email-receiver?color=limegreen

# hive-email-receiver

Email receiver service for Hive.

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/email-receiver
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8
```
