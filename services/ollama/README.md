[![version badge]](https://hub.docker.com/r/gbenson/hive-ollama)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-ollama?color=limegreen

# hive-ollama

Ollama connector service for Hive

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/services/ollama
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
