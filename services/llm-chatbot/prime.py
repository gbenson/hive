import json
import re
import sys


HMC_RE = re.compile(r'"CONTAINER_NAME"\s*:\s*"hive-matrix-connector-\d+"')
NON_JSON_PREFIX = (
    "\x1B[90m<nil>\x1B[0m "
    "\x1B[32mINF\x1B[0m "
    "\x1B[1mReceived\x1B[0m \x1B[36mevent=\x1B[0m"
)

for line in sys.stdin.readlines():
    if not HMC_RE.search(line):
        continue
    entry = json.loads(line)
    raw_message = entry["fields"]["MESSAGE"]
    if raw_message.startswith("{"):
        # JSON
        try:
            msg = json.loads(raw_message)
        except json.JSONDecodeError:
            print(f"\x1B[31m{raw_message[:80]}\x1B[0m")
            continue
        if not (message := msg.get("message")):
            print(f"\x1B[34m{raw_message[:80]}\x1B[0m")
            continue
        if message != "Received":
            continue
        event = msg["event"]
    else:
        # Pre-JSON
        if not raw_message.startswith(NON_JSON_PREFIX):
            if "Received" not in raw_message:
                continue

            assert "Mustafa Khattab" in raw_message
            continue
        raw_event = raw_message.removeprefix(NON_JSON_PREFIX)
        event = json.loads(raw_event)

    event_type = event["type"]
    if event_type != "m.room.message":
        assert event_type == "m.reaction"
        continue
    content = event["content"]
    msgtype = content["msgtype"]
    if msgtype != "m.text":
        assert msgtype == "m.image"
        continue
    #print(content["body"])
