[![version badge]](https://hub.docker.com/r/gbenson/hive-chatbot)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-chatbot?color=limegreen

# hive-chatbot

LangChain chatbot for Hive

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/chatbot
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
