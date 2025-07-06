// Package wrappers provides application-specific Event wrappers.
package wrappers

import (
	"gbenson.net/hive/logging/internal/modifiers"
	"gbenson.net/hive/logging/wrappers/internal"
)

// registerWrapper registers a wrapper with UnmarshalEvent.
var registerWrapper = modifiers.Register

// WrappedEvent is a handy base class for wrapped events.
type wrappedEvent = internal.WrappedEvent
