[![version badge]](https://hub.docker.com/r/gbenson/hive-llm-chatbot)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-llm-chatbot?color=limegreen

# hive-llm-chatbot

LLM chatbot for Hive

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/llm-chatbot
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
make check
```
