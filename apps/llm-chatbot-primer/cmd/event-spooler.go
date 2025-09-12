package main

import (
	"gbenson.net/hive"
	"gbenson.net/hive/apps/llm-chatbot-primer"
)

func main() {
	hive.Run(primer.Main)
}
