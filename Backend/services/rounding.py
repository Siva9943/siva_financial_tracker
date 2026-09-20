"""Centralized rounding policy for all financial calculations (skill §7).

Every monetary Decimal must pass through round_money before being stored,
returned from an API, or used as an input to a later calculation step —
never round implicitly or inconsistently across services.
"""

from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal('0.01')
QUANTITY_UNITS = Decimal('0.000001')
PRICE_UNITS = Decimal('0.0001')


def round_money(value):
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def round_quantity(value):
    return Decimal(value).quantize(QUANTITY_UNITS, rounding=ROUND_HALF_UP)


def round_price(value):
    return Decimal(value).quantize(PRICE_UNITS, rounding=ROUND_HALF_UP)
