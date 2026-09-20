"""Date-range resolution for the dashboard and analytics endpoints (skill §26).

Each range also resolves a "previous period" for trend comparison, chosen to
be the most natural calendar analog rather than a mechanically equal-length
window — a trailing window of the same length only makes sense when there is
no calendar analog (CUSTOM).
"""

from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

RANGES = ('CURRENT_MONTH', 'PREVIOUS_MONTH', 'CURRENT_YEAR', 'CUSTOM')


def month_start(d):
    return d.replace(day=1)


def month_end(d):
    return month_start(d) + relativedelta(months=1) - timedelta(days=1)


def resolve_range(range_key, start=None, end=None, today=None):
    today = today or date.today()

    if range_key == 'CURRENT_MONTH':
        s, e = month_start(today), today
        prev_e = today - relativedelta(months=1)
        prev_s = month_start(prev_e)

    elif range_key == 'PREVIOUS_MONTH':
        anchor = today - relativedelta(months=1)
        s, e = month_start(anchor), month_end(anchor)
        prev_anchor = anchor - relativedelta(months=1)
        prev_s, prev_e = month_start(prev_anchor), month_end(prev_anchor)

    elif range_key == 'CURRENT_YEAR':
        s, e = today.replace(month=1, day=1), today
        prev_s, prev_e = s - relativedelta(years=1), e - relativedelta(years=1)

    elif range_key == 'CUSTOM':
        if not (start and end):
            raise ValueError('A custom range requires both start and end dates.')
        if end < start:
            raise ValueError('end must not be before start.')
        s, e = start, end
        span_days = (e - s).days + 1
        prev_e = s - timedelta(days=1)
        prev_s = prev_e - timedelta(days=span_days - 1)

    else:
        raise ValueError(f'Unknown range "{range_key}". Choose one of {", ".join(RANGES)}.')

    return {'start': s, 'end': e, 'previous_start': prev_s, 'previous_end': prev_e}
