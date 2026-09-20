"""Investment transaction posting — the authoritative holdings ledger (skill §5-7, §31-32).

Design decisions (deliberately documented, since the source spec left them
ambiguous and getting them wrong would silently corrupt every downstream
calculation):

- `amount` on a BUY/SELL transaction is always the PRINCIPAL value of the
  trade (quantity * price), computed here rather than trusted from the
  caller — "never trust frontend calculations" (skill §37). `fees`/`tax`
  are always tracked as separate additive fields on the transaction row and
  are never folded into `total_invested` or `average_buy_price`; they only
  ever enter a calculation at the Total Return step (services to come:
  InvestmentPerformanceService sums `fees`/`tax` across transactions). This
  keeps average_buy_price mathematically clean: it never moves because of
  an unrelated brokerage fee.
- `average_buy_price` is always exactly `total_invested / quantity` for a
  holding — there is no separate "price-only" average tracked anywhere, so
  the two numbers can never drift apart.
- BONUS/SPLIT add free shares (no cash movement): `total_invested` is
  unchanged, `average_buy_price` is diluted by the recompute. Reverse
  splits (reducing share count) are out of scope for this phase and raise
  InvestmentTransactionError rather than guessing at the wrong semantics.
- DEPOSIT/WITHDRAWAL exist for unit-less instruments (Fixed Deposit, Real
  Estate): `quantity` is pinned to a nominal `1` once funded and never
  otherwise tracked; `average_buy_price` mirrors `total_invested` for these
  (there is no per-unit price concept). A WITHDRAWAL is a return of
  capital only — any gain (e.g. FD maturity interest) must be recorded
  separately as a DIVIDEND transaction, never inferred here.
- FEE is a standalone, non-trade cost (e.g. annual account fee): it never
  changes quantity/total_invested/average_buy_price. It exists purely so
  its `fees`/`tax` value is included in the Total Return fee deduction.
"""

from datetime import date
from decimal import Decimal

from django.db import transaction as db_transaction

from .rounding import round_money, round_price, round_quantity

ZERO = Decimal('0.00')


class InvestmentTransactionError(Exception):
    """Raised for business-rule violations the caller should surface as a 400."""


def _validate_common(investment, transaction_type, transaction_date, fees, tax, today):
    today = today or date.today()
    if transaction_date > today:
        raise InvestmentTransactionError('Transaction date cannot be in the future.')
    if fees < 0:
        raise InvestmentTransactionError('Fees cannot be negative.')
    if tax < 0:
        raise InvestmentTransactionError('Tax cannot be negative.')


def _recompute_average(total_invested, quantity):
    if quantity <= 0:
        return ZERO
    return round_price(total_invested / quantity)


def _apply_buy(investment, quantity, price):
    if quantity is None or quantity <= 0:
        raise InvestmentTransactionError('Quantity must be greater than zero for a BUY.')
    if price is None or price <= 0:
        raise InvestmentTransactionError('Price must be greater than zero for a BUY.')

    amount = round_money(quantity * price)
    new_quantity = investment.quantity + quantity
    new_total_invested = round_money(investment.total_invested + amount)

    investment.quantity = new_quantity
    investment.total_invested = new_total_invested
    investment.average_buy_price = _recompute_average(new_total_invested, new_quantity)
    if investment.status == investment.Status.CLOSED:
        investment.status = investment.Status.ACTIVE

    return amount


def _apply_sell(investment, quantity, price):
    if quantity is None or quantity <= 0:
        raise InvestmentTransactionError('Quantity must be greater than zero for a SELL.')
    if price is None or price <= 0:
        raise InvestmentTransactionError('Price must be greater than zero for a SELL.')
    if investment.status == investment.Status.CLOSED or investment.quantity <= 0:
        raise InvestmentTransactionError('This investment has no holdings to sell.')
    if quantity > investment.quantity:
        raise InvestmentTransactionError(
            f'Cannot sell {quantity} units — only {investment.quantity} are held.'
        )

    amount = round_money(quantity * price)
    cost_basis_sold = round_money(investment.average_buy_price * quantity)
    realized_gain = round_money(amount - cost_basis_sold)

    new_quantity = investment.quantity - quantity
    investment.realized_profit_loss = round_money(investment.realized_profit_loss + realized_gain)
    investment.quantity = new_quantity

    if new_quantity <= 0:
        investment.total_invested = ZERO
        investment.average_buy_price = ZERO
        investment.status = investment.Status.CLOSED
    else:
        investment.total_invested = round_money(investment.total_invested - cost_basis_sold)

    return amount


def _apply_dividend(investment, amount):
    if amount is None or amount <= 0:
        raise InvestmentTransactionError('Amount must be greater than zero for a DIVIDEND.')
    investment.dividend_income = round_money(investment.dividend_income + amount)
    return round_money(amount)


def _apply_bonus_or_split(investment, quantity):
    if quantity is None or quantity <= 0:
        raise InvestmentTransactionError('Quantity must be greater than zero for BONUS/SPLIT (reverse splits are not supported).')
    new_quantity = investment.quantity + quantity
    investment.quantity = new_quantity
    investment.average_buy_price = _recompute_average(investment.total_invested, new_quantity)
    return ZERO


def _apply_fee(fees, tax):
    if fees <= 0 and tax <= 0:
        raise InvestmentTransactionError('A FEE transaction must have a positive fee or tax amount.')
    return ZERO


def _apply_deposit(investment, amount):
    if amount is None or amount <= 0:
        raise InvestmentTransactionError('Amount must be greater than zero for a DEPOSIT.')

    new_total_invested = round_money(investment.total_invested + amount)
    # Only pin quantity to a nominal 1 the first time this investment is funded (quantity
    # was 0 — a Fixed Deposit/Real Estate style holding with no share count). If quantity is
    # already >0 (e.g. a stock funded via BUY transactions), leave it untouched — forcing it
    # to 1 would silently corrupt a real share count.
    new_quantity = investment.quantity if investment.quantity > 0 else Decimal('1')

    investment.total_invested = new_total_invested
    investment.quantity = new_quantity
    investment.average_buy_price = _recompute_average(new_total_invested, new_quantity)
    if investment.status == investment.Status.CLOSED:
        investment.status = investment.Status.ACTIVE
    return round_money(amount)


def _apply_withdrawal(investment, amount):
    if amount is None or amount <= 0:
        raise InvestmentTransactionError('Amount must be greater than zero for a WITHDRAWAL.')
    if investment.status == investment.Status.CLOSED or investment.total_invested <= 0:
        raise InvestmentTransactionError('This investment has no invested balance to withdraw.')
    if amount > investment.total_invested:
        raise InvestmentTransactionError(
            f'Cannot withdraw {amount} — only {investment.total_invested} is invested.'
        )

    new_total_invested = round_money(investment.total_invested - amount)
    investment.total_invested = new_total_invested
    if new_total_invested <= 0:
        investment.quantity = ZERO
        investment.average_buy_price = ZERO
        investment.status = investment.Status.CLOSED
    else:
        # Quantity is left untouched (a WITHDRAWAL is a cash-only return of capital) —
        # only the average cost basis per unit shrinks accordingly.
        investment.average_buy_price = _recompute_average(new_total_invested, investment.quantity)

    return round_money(amount)


def record_investment_transaction(
    investment,
    *,
    transaction_type,
    transaction_date,
    quantity=None,
    price=None,
    amount=None,
    fees=None,
    tax=None,
    reference='',
    notes='',
    today=None,
):
    """Validate and post a transaction, atomically updating the investment's cached holdings.

    Returns the created InvestmentTransaction. `amount` is authoritative
    only for DIVIDEND/DEPOSIT/WITHDRAWAL — for every other type it is
    computed here and any caller-supplied value is ignored.
    """
    TransactionType = investment.transactions.model.TransactionType

    fees = round_money(fees) if fees is not None else ZERO
    tax = round_money(tax) if tax is not None else ZERO
    quantity = round_quantity(quantity) if quantity is not None else None
    price = round_price(price) if price is not None else None

    _validate_common(investment, transaction_type, transaction_date, fees, tax, today)

    if transaction_type == TransactionType.BUY:
        resolved_amount = _apply_buy(investment, quantity, price)
    elif transaction_type == TransactionType.SELL:
        resolved_amount = _apply_sell(investment, quantity, price)
    elif transaction_type == TransactionType.DIVIDEND:
        resolved_amount = _apply_dividend(investment, amount)
    elif transaction_type in (TransactionType.BONUS, TransactionType.SPLIT):
        resolved_amount = _apply_bonus_or_split(investment, quantity)
        quantity = round_quantity(quantity)
        price = ZERO
    elif transaction_type == TransactionType.FEE:
        resolved_amount = _apply_fee(fees, tax)
        quantity = ZERO
        price = ZERO
    elif transaction_type == TransactionType.DEPOSIT:
        resolved_amount = _apply_deposit(investment, amount)
        quantity = ZERO
        price = ZERO
    elif transaction_type == TransactionType.WITHDRAWAL:
        resolved_amount = _apply_withdrawal(investment, amount)
        quantity = ZERO
        price = ZERO
    else:
        raise InvestmentTransactionError(f'Unknown transaction type "{transaction_type}".')

    with db_transaction.atomic():
        txn = investment.transactions.create(
            user=investment.user,
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            quantity=quantity or ZERO,
            price=price or ZERO,
            amount=resolved_amount,
            fees=fees,
            tax=tax,
            reference=reference,
            notes=notes,
        )
        investment.save(
            update_fields=[
                'quantity', 'total_invested', 'average_buy_price',
                'realized_profit_loss', 'dividend_income', 'status', 'updated_at',
            ]
        )

    return txn
