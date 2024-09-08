# Hive

## Invocation

Normal (production, hardened) startup:

```sh
docker compose up -d
```

Start with exposed RabbitMQ ports, for development and testing:

```sh
HIVE_ISOLATE_RABBITMQ=false docker compose up -d
```

## Development

### Python

You can create per-project virtual environments or use the same one for
everything, it's up to you.  Either way you should install the common
cross-package dependencies (listed in `requirements.txt`) as follows:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install wheel
pip install -r requirements.txt
```
