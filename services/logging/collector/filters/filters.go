// Package filters allows excluding events from forwarding.
package filters

import "gbenson.net/hive/services/logging/collector/filters/mongo"

// This package is a last-resort to handle message spam that cannot
// otherwise be configured out.  Strive to avoid adding to it!

func ShouldForwardEvent(event map[string]string) bool {
	if mongo.IsMongoNoise(event) {
		return false
	}

	return true
}
