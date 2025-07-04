package internal

import . "gbenson.net/hive/logging/event"

type PriorityMap map[any]Priority

func (m PriorityMap) Get(v any) Priority {
	if p, ok := m[v]; ok {
		return p
	}
	return PriUnknown
}
