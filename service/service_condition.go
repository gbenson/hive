package service

type ServiceCondition int

const (
	ConditionHealthy ServiceCondition = iota
	ConditionDubious
	ConditionInError
	ConditionUnmonitored
)

func (c ServiceCondition) String() string {
	switch c {
	case ConditionHealthy:
		return "healthy"
	case ConditionDubious:
		return "dubious"
	default:
		return "in_error"
	}
}
