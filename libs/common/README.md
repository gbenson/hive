[![version badge]](https://pypi.org/project/hive-common/)

[version badge]: https://img.shields.io/pypi/v/hive-common?color=limegreen

# hive-common

Common code for Hive libraries and services

## Installation

### With PIP

```sh
pip install hive-common
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
