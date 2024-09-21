[![version badge]](https://pypi.org/project/hive-service/)

[version badge]: https://img.shields.io/pypi/v/hive-service?color=limegreen

# hive-service

Common code for Hive services

## Installation

### With PIP

```sh
pip install hive-service
```

### From source

```sh
git clone https://github.com/gbenson/hive.git
cd hive/libs/service
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
