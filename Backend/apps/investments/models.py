from django.conf import settings
from django.db import models


class Investment(models.Model):
    class InvestmentType(models.TextChoices):
        STOCK = 'STOCK', 'Stock'
        MUTUAL_FUND = 'MUTUAL_FUND', 'Mutual Fund'
        ETF = 'ETF', 'ETF'
        BOND = 'BOND', 'Bond'
        FIXED_DEPOSIT = 'FIXED_DEPOSIT', 'Fixed Deposit'
        GOLD = 'GOLD', 'Gold'
        CRYPTO = 'CRYPTO', 'Crypto'
        REAL_ESTATE = 'REAL_ESTATE', 'Real Estate'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        ON_HOLD = 'ON_HOLD', 'On Hold'
        CLOSED = 'CLOSED', 'Closed'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investments')
    name = models.CharField(max_length=150)
    symbol = models.CharField(max_length=30, blank=True)
    investment_type = models.CharField(max_length=20, choices=InvestmentType.choices)
    platform = models.CharField(max_length=100, blank=True)

    # Cached holdings, recomputed by services.investment_service.apply_transaction() inside
    # transaction.atomic() whenever a transaction is posted — never written to directly by a
    # serializer or view. current_value / unrealized_profit_loss are deliberately NOT stored
    # here: they're always quantity * current_price and current_value - total_invested,
    # computed on read, so they can never drift out of sync with current_price.
    quantity = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    average_buy_price = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    total_invested = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    realized_profit_loss = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    dividend_income = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    # Manually maintained (skill: no external market-data dependency for core functionality).
    current_price = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    current_price_updated_at = models.DateTimeField(null=True, blank=True)

    linked_goal = models.ForeignKey(
        'goals.FinancialGoal', null=True, blank=True, on_delete=models.SET_NULL, related_name='investments'
    )

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=('user', 'status')),
            models.Index(fields=('user', 'investment_type')),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gte=0), name='investment_quantity_non_negative'),
            models.CheckConstraint(condition=models.Q(average_buy_price__gte=0), name='investment_avg_buy_price_non_negative'),
            models.CheckConstraint(condition=models.Q(current_price__gte=0), name='investment_current_price_non_negative'),
            models.CheckConstraint(condition=models.Q(total_invested__gte=0), name='investment_total_invested_non_negative'),
        ]

    def __str__(self):
        return f'{self.name} ({self.user_id})'


class InvestmentTransaction(models.Model):
    class TransactionType(models.TextChoices):
        BUY = 'BUY', 'Buy'
        SELL = 'SELL', 'Sell'
        DIVIDEND = 'DIVIDEND', 'Dividend'
        BONUS = 'BONUS', 'Bonus'
        SPLIT = 'SPLIT', 'Split'
        FEE = 'FEE', 'Fee'
        DEPOSIT = 'DEPOSIT', 'Deposit'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'

    # Denormalized directly onto the transaction (same pattern as apps.transactions.Transaction)
    # so ownership checks and per-user queries never need to join through `investment`.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investment_transactions')
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='transactions')

    transaction_type = models.CharField(max_length=12, choices=TransactionType.choices)
    transaction_date = models.DateField()

    quantity = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    price = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    fees = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-transaction_date', '-created_at')
        indexes = [
            models.Index(fields=('user', 'transaction_date')),
            models.Index(fields=('investment', 'transaction_date')),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gte=0), name='investment_txn_quantity_non_negative'),
            models.CheckConstraint(condition=models.Q(price__gte=0), name='investment_txn_price_non_negative'),
            # >=0 rather than >0: BONUS/SPLIT corporate actions move shares with zero cash amount.
            # services.investment_service enforces amount > 0 for the cash-moving transaction types.
            models.CheckConstraint(condition=models.Q(amount__gte=0), name='investment_txn_amount_non_negative'),
            models.CheckConstraint(condition=models.Q(fees__gte=0), name='investment_txn_fees_non_negative'),
            models.CheckConstraint(condition=models.Q(tax__gte=0), name='investment_txn_tax_non_negative'),
        ]

    def __str__(self):
        return f'{self.transaction_type} {self.amount} on {self.transaction_date} for investment {self.investment_id}'


class PortfolioSnapshot(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolio_snapshots')
    snapshot_date = models.DateField()

    total_invested = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    portfolio_value = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    # Reserved for a future cash/uninvested-balance concept — unused by phase 1 services.
    cash_value = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    profit_loss = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    dividend_income = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-snapshot_date',)
        indexes = [models.Index(fields=('user', 'snapshot_date'))]
        constraints = [
            models.UniqueConstraint(fields=('user', 'snapshot_date'), name='unique_portfolio_snapshot_per_user_day'),
        ]

    def __str__(self):
        return f'Snapshot for {self.user_id} on {self.snapshot_date}'
