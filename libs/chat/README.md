[![version badge]](https://pypi.org/project/hive-chat/)

[version badge]: https://img.shields.io/pypi/v/hive-chat?color=limegreen

# hive-chat

Chatbot interface for Hive

## Installation

### With PIP

```sh
pip install hive-chat
```

### From source

```sh
git clone https://github.com/gbenson/hive.git
cd hive/libs/chat
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
