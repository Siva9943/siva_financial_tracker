"""Loan payment recording workflow (skill §12).

Every step — interest allocation, principal reduction, fee handling,
outstanding-balance update, and the linked ledger Transaction — happens
inside one atomic block. No partial updates are ever persisted.
"""

from decimal import Decimal

from django.db import transaction as db_transaction

from apps.loans.date_utils import advance_date
from apps.loans.models import Loan, LoanPayment
from apps.loans.schedule import compute_next_installment
from apps.transactions.models import Transaction

from .rounding import round_money


class LoanPaymentError(Exception):
    """Raised for business-rule violations the caller should surface as a 400."""


def record_loan_payment(loan, *, payment_date, amount, late_fee=None, payment_method='OTHER', transaction_reference='', notes=''):
    if loan.status not in (Loan.Status.ACTIVE, Loan.Status.OVERDUE):
        raise LoanPaymentError(f'Cannot record a payment on a loan with status {loan.status}.')

    if loan.outstanding_principal <= 0:
        raise LoanPaymentError('This loan has no outstanding balance.')

    amount = round_money(amount)

    last_payment = loan.payments.order_by('-payment_date', '-created_at').first()
    accrual_start_date = last_payment.payment_date if last_payment else loan.start_date

    installment = compute_next_installment(loan, accrual_start_date=accrual_start_date, payment_date=payment_date)
    interest_due = installment['interest']
    scheduled_principal = installment['scheduled_principal']

    if late_fee is not None:
        late_fee_amount = round_money(late_fee)
    elif loan.next_due_date and payment_date > loan.next_due_date:
        late_fee_amount = round_money(loan.late_fee)
    else:
        late_fee_amount = Decimal('0.00')

    if late_fee_amount > amount:
        raise LoanPaymentError('Late fee cannot exceed the payment amount.')

    available = amount - late_fee_amount
    interest_component = min(available, interest_due)
    principal_component = available - interest_component

    if principal_component > loan.outstanding_principal:
        max_payoff = round_money(interest_component + loan.outstanding_principal + late_fee_amount)
        raise LoanPaymentError(
            f'Payment exceeds what is needed to close this loan. Maximum payoff amount is {max_payoff}.'
        )

    extra_payment = max(Decimal('0.00'), principal_component - scheduled_principal)
    remaining_principal = round_money(loan.outstanding_principal - principal_component)

    with db_transaction.atomic():
        payment_transaction = Transaction.objects.create(
            user=loan.user,
            transaction_type=Transaction.TransactionType.LOAN_PAYMENT,
            amount=amount,
            category=loan.loan_name,
            description=f'Payment for {loan.loan_name}',
            transaction_date=payment_date,
            payment_method=payment_method,
            reference=transaction_reference,
        )

        loan_payment = LoanPayment.objects.create(
            loan=loan,
            payment_date=payment_date,
            amount=amount,
            principal_component=round_money(principal_component),
            interest_component=round_money(interest_component),
            late_fee=late_fee_amount,
            extra_payment=round_money(extra_payment),
            remaining_principal=remaining_principal,
            transaction=payment_transaction,
            transaction_reference=transaction_reference,
            notes=notes,
        )

        loan.outstanding_principal = remaining_principal
        if remaining_principal <= 0:
            loan.status = Loan.Status.COMPLETED
            loan.next_due_date = None
        else:
            loan.next_due_date = advance_date(loan.next_due_date or payment_date, loan.payment_frequency)
            if loan.status == Loan.Status.OVERDUE:
                loan.status = Loan.Status.ACTIVE
        loan.save(update_fields=['outstanding_principal', 'status', 'next_due_date', 'updated_at'])

    return loan_payment
