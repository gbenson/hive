package service

type ServiceCondition int

const (
	ConditionUnset ServiceCondition = iota
	ConditionHealthy
	ConditionDubious
	ConditionInError
)

func (c ServiceCondition) String() string {
	switch c {
	case ConditionHealthy:
		return "HEALTHY"
	case ConditionDubious:
		return "DUBIOUS"
	default:
		return "IN_ERROR"
	}
}
