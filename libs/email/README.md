[![version badge]](https://pypi.org/project/hive-email/)

[version badge]: https://img.shields.io/pypi/v/hive-email?color=limegreen

# hive-email

Email message handling for Hive.

## Installation

### With PIP

```sh
pip install hive-email
```

### From source

```sh
git clone https://github.com/gbenson/hive.git
cd hive/libs/email
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
