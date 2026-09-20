from decimal import Decimal

from rest_framework import serializers

from services.goal_service import calculate_goal_progress

from .models import FinancialGoal, GoalContribution


class FinancialGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialGoal
        fields = (
            'id',
            'name',
            'goal_type',
            'target_amount',
            'current_amount',
            'target_date',
            'monthly_contribution',
            'priority',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'status', 'created_at', 'updated_at')

    def validate_target_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Target amount must be greater than zero.')
        return value

    def validate_current_amount(self, value):
        if value < 0:
            raise serializers.ValidationError('Current amount cannot be negative.')
        return value

    def validate_monthly_contribution(self, value):
        if value < 0:
            raise serializers.ValidationError('Monthly contribution cannot be negative.')
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(calculate_goal_progress(instance))
        return data


class GoalContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalContribution
        fields = ('id', 'amount', 'contribution_date', 'notes', 'created_at')
        read_only_fields = fields


class GoalContributionCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))
    contribution_date = serializers.DateField()
    notes = serializers.CharField(required=False, allow_blank=True, default='')
