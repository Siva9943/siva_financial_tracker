from django.utils import timezone
from rest_framework import serializers

from apps.goals.models import FinancialGoal
from services.investment_performance_service import get_investment_performance

from .models import Investment, InvestmentTransaction, PortfolioSnapshot


class InvestmentSerializer(serializers.ModelSerializer):
    linked_goal = serializers.PrimaryKeyRelatedField(queryset=FinancialGoal.objects.none(), required=False, allow_null=True)

    class Meta:
        model = Investment
        fields = (
            'id', 'name', 'symbol', 'investment_type', 'platform',
            'quantity', 'average_buy_price', 'total_invested',
            'realized_profit_loss', 'dividend_income',
            'current_price', 'current_price_updated_at',
            'linked_goal', 'status', 'notes', 'created_at', 'updated_at',
        )
        # quantity/average_buy_price/total_invested/realized_profit_loss/dividend_income are
        # only ever written by services.investment_service.record_investment_transaction —
        # never directly through this serializer. `status` IS user-writable (so an investment
        # can be manually put ON_HOLD, mirroring Loan.status/PAUSED) but the transaction
        # service still auto-manages the ACTIVE<->CLOSED transitions on BUY/SELL/DEPOSIT/
        # WITHDRAWAL — see investment_service for that logic. `current_price_updated_at` is
        # never client-writable — see update() below, which stamps it automatically whenever
        # current_price actually changes.
        read_only_fields = (
            'id', 'quantity', 'average_buy_price', 'total_invested',
            'realized_profit_loss', 'dividend_income', 'current_price_updated_at',
            'created_at', 'updated_at',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request is not None:
            self.fields['linked_goal'].queryset = FinancialGoal.objects.filter(user=request.user)

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('Name is required.')
        return value

    def validate_current_price(self, value):
        if value < 0:
            raise serializers.ValidationError('Current price cannot be negative.')
        return value

    def update(self, instance, validated_data):
        if 'current_price' in validated_data and validated_data['current_price'] != instance.current_price:
            instance.current_price_updated_at = timezone.now()
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # N+1 note (skill §34): each row runs its own small aggregate query for
        # fees/tax. Acceptable for typical portfolio sizes (tens of holdings);
        # revisit with a bulk-prefetch variant if that assumption stops holding.
        data.update(get_investment_performance(instance))
        return data


class InvestmentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentTransaction
        fields = ('id', 'transaction_type', 'transaction_date', 'quantity', 'price', 'amount', 'fees', 'tax', 'reference', 'notes', 'created_at')
        read_only_fields = fields


class DividendSerializer(serializers.ModelSerializer):
    investment_id = serializers.IntegerField(source='investment.id')
    investment_name = serializers.CharField(source='investment.name')

    class Meta:
        model = InvestmentTransaction
        fields = ('id', 'investment_id', 'investment_name', 'transaction_date', 'amount', 'reference', 'notes')
        read_only_fields = fields


class PortfolioSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioSnapshot
        fields = ('id', 'snapshot_date', 'total_invested', 'portfolio_value', 'profit_loss', 'dividend_income')
        read_only_fields = fields


class InvestmentTransactionCreateSerializer(serializers.Serializer):
    transaction_type = serializers.ChoiceField(choices=InvestmentTransaction.TransactionType.choices)
    transaction_date = serializers.DateField()
    quantity = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, allow_null=True)
    price = serializers.DecimalField(max_digits=14, decimal_places=4, required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=16, decimal_places=2, required=False, allow_null=True)
    fees = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    tax = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    reference = serializers.CharField(required=False, allow_blank=True, default='')
    notes = serializers.CharField(required=False, allow_blank=True, default='')
