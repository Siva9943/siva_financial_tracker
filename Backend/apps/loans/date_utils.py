from dateutil.relativedelta import relativedelta

PERIODS_PER_YEAR = {
    'WEEKLY': 52,
    'BIWEEKLY': 26,
    'MONTHLY': 12,
    'QUARTERLY': 4,
    'YEARLY': 1,
}

_STEP = {
    'WEEKLY': relativedelta(weeks=1),
    'BIWEEKLY': relativedelta(weeks=2),
    'MONTHLY': relativedelta(months=1),
    'QUARTERLY': relativedelta(months=3),
    'YEARLY': relativedelta(years=1),
}


def advance_date(date, frequency):
    """Advance `date` by one payment period, correctly handling month-end/leap-year rollover."""
    return date + _STEP[frequency]


def count_periods(start_date, end_date, frequency):
    """Count whole payment periods between two dates at the given frequency."""
    periods = 0
    current = start_date
    while True:
        next_date = advance_date(current, frequency)
        if next_date > end_date:
            break
        periods += 1
        current = next_date
    return periods
