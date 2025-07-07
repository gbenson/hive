package rxp

const (
	DayOfMonth = `[0-3]\d`
	Month      = `[012]\d`
	Year       = `\d{4}`
	Hour       = `[012]\d`
	Minute     = `[0-5]\d`
	Second     = `[0-6]\d`

	ShortMonthName = `[ADFJMNOS][aceopu][bcglnprtvy]`
	Zone           = `[+-][01]\d` + Minute

	SlashDate_YYYYmmdd  = Year + `/` + Month + `/` + DayOfMonth
	SlashDate_ddbbbYYYY = DayOfMonth + `/` + ShortMonthName + `/` + Year

	ColonTime_HHMMSS = Hour + `:` + Minute + `:` + Second
)
