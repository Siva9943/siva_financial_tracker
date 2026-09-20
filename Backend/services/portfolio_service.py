"""Cross-investment portfolio views: holdings table and allocation breakdowns.

Per-holding return figures are delegated to investment_performance_service
so there is exactly one implementation of the return formula in the codebase.
"""

from decimal import Decimal

from .investment_performance_service import get_investment_performance
from .rounding import round_money

ZERO = Decimal('0.00')


def build_holdings(queryset):
    """One row per investment, combining its stored fields with computed performance."""
    holdings = []
    for investment in queryset:
        performance = get_investment_performance(investment)
        holdings.append(
            {
                'id': investment.id,
                'name': investment.name,
                'symbol': investment.symbol,
                'investment_type': investment.investment_type,
                'platform': investment.platform,
                'status': investment.status,
                'quantity': investment.quantity,
                'average_buy_price': investment.average_buy_price,
                'current_price': investment.current_price,
                **performance,
            }
        )
    return holdings


def _allocation_from_holdings(holdings, group_key):
    totals = {}
    for holding in holdings:
        if holding['status'] != 'ACTIVE' or holding['current_value'] <= 0:
            continue
        key = holding[group_key] or 'Unspecified'
        totals[key] = totals.get(key, ZERO) + holding['current_value']

    grand_total = sum(totals.values(), ZERO)
    rows = [{'label': label, 'current_value': round_money(total)} for label, total in totals.items()]
    rows.sort(key=lambda row: row['current_value'], reverse=True)
    for row in rows:
        row['percentage'] = round(float(row['current_value']) / float(grand_total) * 100, 2) if grand_total else 0
    return rows


def allocation_by_type(holdings):
    return _allocation_from_holdings(holdings, 'investment_type')


def allocation_by_platform(holdings):
    return _allocation_from_holdings(holdings, 'platform')
