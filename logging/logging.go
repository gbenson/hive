// Package logging provides centralized logging services for Hive.
package logging

import (
	"gbenson.net/hive/logging/internal/logger"
	"gbenson.net/hive/logging/internal/modifiers"
	"gbenson.net/hive/logging/internal/unmarshal"
	_ "gbenson.net/hive/logging/wrappers"
)

// An EventModifier returns a new modified event or returns the
// original event unmodified.
type EventModifier = modifiers.EventModifier

// RegisterModifier registers an event modifier.
var RegisterModifier = modifiers.Register

// SetLogger specifies an optional logger for reporting errors that
// would otherwise be silently ignored.  Be careful to avoid loops
// when enabling this!
var SetLogger = logger.SetLogger

// UnmarshalEvent unmarshals a messaging event into a logging event.
var UnmarshalEvent = unmarshal.UnmarshalEvent
