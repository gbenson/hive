[![version badge]](https://pypi.org/project/hive-config/)

[version badge]: https://img.shields.io/pypi/v/hive-config?color=limegreen

# hive-config

Configuration management for Hive.

## Installation

### With PIP

```sh
pip install hive-config
```

### From source

```sh
git clone https://github.com/gbenson/hive.git
cd hive/libs/common
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
