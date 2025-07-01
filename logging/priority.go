package logging

import . "gbenson.net/hive/logging/event"

type priorityMap map[any]Priority

func (m priorityMap) Get(v any) Priority {
	if p, ok := m[v]; ok {
		return p
	}
	return PriUnknown
}
