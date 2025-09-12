# llm-chatbot-primer

LLM chatbot database primer for Hive

## Setup

```sh
git clone https://github.com/gbenson/hive.git
cd apps/llm-chatbot-primer
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### Operation

```sh
rm -f llm-chatbot-requests.jsonl
go run ./cmd/event-spooler.go | llm-chatbot-primer
llm-chatbot-filler < llm-chatbot-requests.jsonl
```
