"""Investment & portfolio return calculations (skill §6, §7, §20).

Everything here is computed fresh from the Investment's cached holdings
fields plus its own transaction history — nothing is persisted, so nothing
here can go stale on its own (current_price changes take effect the moment
it's next read).

Methodology is explicitly labeled `AVERAGE_COST_SIMPLE_RETURN`: a
percentage-of-cost-basis return, NOT a time-weighted or money-weighted
return. XIRR/TWR are out of scope for this phase (skill §21) — if added
later they must be separate, clearly-labeled service functions rather than
a change to this one's output shape.

Closed-position nuance: once an investment is fully sold, its cached
`total_invested` is (correctly) zero — there is no live cost basis left to
report a percentage against. For that case only, this module falls back to
`lifetime_cost_basis`: the sum of every BUY/DEPOSIT transaction's amount
ever recorded for that investment, read directly from history rather than
from any cached field.
"""

from decimal import Decimal

from django.db.models import Sum

from apps.investments.models import Investment, InvestmentTransaction

from .rounding import round_money

ZERO = Decimal('0.00')
METHODOLOGY = 'AVERAGE_COST_SIMPLE_RETURN'

_COST_BASIS_TYPES = (InvestmentTransaction.TransactionType.BUY, InvestmentTransaction.TransactionType.DEPOSIT)


def _lifetime_cost_basis(investment):
    total = investment.transactions.filter(transaction_type__in=_COST_BASIS_TYPES).aggregate(total=Sum('amount'))['total']
    return round_money(total or ZERO)


def _fees_and_tax(investment_or_queryset):
    totals = investment_or_queryset.aggregate(fees=Sum('fees'), tax=Sum('tax'))
    return round_money(totals['fees'] or ZERO), round_money(totals['tax'] or ZERO)


def get_investment_performance(investment):
    """Return the full return breakdown for a single Investment."""
    current_value = round_money(investment.quantity * investment.current_price)
    unrealized_profit_loss = round_money(current_value - investment.total_invested)
    capital_gain = round_money(investment.realized_profit_loss + unrealized_profit_loss)

    total_fees, total_tax = _fees_and_tax(investment.transactions)
    total_return = round_money(capital_gain + investment.dividend_income - total_fees - total_tax)

    cost_basis = investment.total_invested if investment.total_invested > 0 else _lifetime_cost_basis(investment)
    return_percentage = round(float(total_return) / float(cost_basis) * 100, 2) if cost_basis else 0.0

    return {
        'current_value': current_value,
        'total_invested': investment.total_invested,
        'unrealized_profit_loss': unrealized_profit_loss,
        'realized_profit_loss': investment.realized_profit_loss,
        'dividend_income': investment.dividend_income,
        'total_fees': total_fees,
        'total_tax': total_tax,
        'capital_gain': capital_gain,
        'total_return': total_return,
        'return_percentage': return_percentage,
        'methodology': METHODOLOGY,
    }


def get_portfolio_performance(user):
    """Return the same breakdown aggregated across every investment a user owns."""
    investments = Investment.objects.filter(user=user)
    total_fees, total_tax = _fees_and_tax(InvestmentTransaction.objects.filter(user=user))

    current_value = ZERO
    total_invested = ZERO
    realized_profit_loss = ZERO
    dividend_income = ZERO

    for investment in investments:
        current_value += round_money(investment.quantity * investment.current_price)
        total_invested += investment.total_invested
        realized_profit_loss += investment.realized_profit_loss
        dividend_income += investment.dividend_income

    current_value = round_money(current_value)
    unrealized_profit_loss = round_money(current_value - total_invested)
    capital_gain = round_money(realized_profit_loss + unrealized_profit_loss)
    total_return = round_money(capital_gain + dividend_income - total_fees - total_tax)

    cost_basis = total_invested if total_invested > 0 else _lifetime_cost_basis_for_user(user)
    return_percentage = round(float(total_return) / float(cost_basis) * 100, 2) if cost_basis else 0.0

    return {
        'total_invested': round_money(total_invested),
        'current_value': current_value,
        'unrealized_profit_loss': unrealized_profit_loss,
        'realized_profit_loss': round_money(realized_profit_loss),
        'dividend_income': round_money(dividend_income),
        'total_fees': total_fees,
        'total_tax': total_tax,
        'capital_gain': capital_gain,
        'total_return': total_return,
        'return_percentage': return_percentage,
        'investment_count': investments.count(),
        'methodology': METHODOLOGY,
    }


def _lifetime_cost_basis_for_user(user):
    total = InvestmentTransaction.objects.filter(user=user, transaction_type__in=_COST_BASIS_TYPES).aggregate(
        total=Sum('amount')
    )['total']
    return round_money(total or ZERO)
