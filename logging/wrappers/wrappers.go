// Package wrappers provides application-specific Event wrappers.
package wrappers

import "gbenson.net/hive/logging/internal/modifiers"

// registerWrapper registers a wrapper with UnmarshalEvent.
var registerWrapper = modifiers.Register
