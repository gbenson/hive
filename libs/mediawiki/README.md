[![version badge]](https://pypi.org/project/hive-mediawiki/)

[version badge]: https://img.shields.io/pypi/v/hive-mediawiki?color=limegreen

# hive-mediawiki

MediaWiki interface for Hive.

## Installation

### With PIP

```sh
pip install hive-mediawiki
```

### From source

```sh
git clone https://github.com/gbenson/hive.git
cd hive/libs/mediawiki
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
