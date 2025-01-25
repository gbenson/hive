[![version badge]](https://hub.docker.com/r/gbenson/hive-local-llm)

[version badge]: https://img.shields.io/docker/v/gbenson/hive-local-llm?color=limegreen

# hive-local-llm

Local LLM for Hive

## Installation

### For development

```sh
git clone https://github.com/gbenson/hive.git
cd hive/locals/local-llm
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
flake8 && pytest
```
