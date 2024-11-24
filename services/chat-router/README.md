[![version badge]](https://hub.docker.com/r/gbenson/hive-chat-router)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-chat-router?color=limegreen

# hive-chat-router

Chat message router for Hive

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/chat-router
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
