[![version badge]](https://pypi.org/project/hive-messaging/)

[version badge]: https://img.shields.io/pypi/v/hive-messaging?color=limegreen

# hive-messaging

Messaging layer for Hive.

## Installation

### With PIP

```sh
pip install hive-messaging
```

### From source

```sh
git clone https://github.com/gbenson/hive.git
cd hive/libs/messaging
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
