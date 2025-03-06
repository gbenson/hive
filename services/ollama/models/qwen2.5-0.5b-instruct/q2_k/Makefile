MODEL = "gbenson/qwen2.5-0.5b-instruct:q2_k"

build:
	ollama create $(MODEL)

run:
	ollama run --verbose $(MODEL)

push:
	ollama push $(MODEL)


.PHONY: build run push
