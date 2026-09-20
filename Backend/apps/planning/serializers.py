from decimal import Decimal

from rest_framework import serializers

from .models import PlanItem, RepaymentPlan


class RepaymentPlanGenerateSerializer(serializers.Serializer):
    strategy = serializers.ChoiceField(choices=RepaymentPlan.Strategy.choices)
    monthly_income = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))
    essential_expenses = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)
    emergency_savings_allocation = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=Decimal('0'))
    extra_payment = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0, default=Decimal('0'))


class PlanItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanItem
        fields = (
            'month_number',
            'month_date',
            'loan',
            'loan_name',
            'normal_emi',
            'extra_payment',
            'principal_paid',
            'interest_paid',
            'closing_balance',
        )


class RepaymentPlanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepaymentPlan
        fields = (
            'id',
            'strategy',
            'monthly_income',
            'essential_expenses',
            'emergency_savings_allocation',
            'extra_payment',
            'total_existing_emi',
            'months_remaining',
            'expected_payoff_date',
            'total_interest',
            'total_payment',
            'created_at',
        )


class RepaymentPlanDetailSerializer(RepaymentPlanListSerializer):
    items = PlanItemSerializer(many=True, read_only=True)

    class Meta(RepaymentPlanListSerializer.Meta):
        fields = RepaymentPlanListSerializer.Meta.fields + ('assumptions', 'items')
