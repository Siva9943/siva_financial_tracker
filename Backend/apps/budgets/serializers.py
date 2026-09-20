from rest_framework import serializers

from services.budget_service import calculate_budget_usage, get_spent_for_budget

from .models import Budget


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ('id', 'category', 'amount', 'month', 'year', 'alert_thresholds', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Budget amount must be greater than zero.')
        return value

    def validate_month(self, value):
        if not 1 <= value <= 12:
            raise serializers.ValidationError('Month must be between 1 and 12.')
        return value

    def validate_category(self, value):
        if not value.strip():
            raise serializers.ValidationError('Category is required.')
        return value

    def validate_alert_thresholds(self, value):
        if not value:
            raise serializers.ValidationError('At least one alert threshold is required.')
        for threshold in value:
            if not (0 < threshold <= 100):
                raise serializers.ValidationError('Each threshold must be between 1 and 100.')
        return sorted(set(value))

    def validate(self, attrs):
        category = attrs.get('category', getattr(self.instance, 'category', None))
        month = attrs.get('month', getattr(self.instance, 'month', None))
        year = attrs.get('year', getattr(self.instance, 'year', None))

        request = self.context.get('request')
        if request is not None:
            queryset = Budget.objects.filter(user=request.user, category=category, month=month, year=year)
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {'category': f'A budget for "{category}" already exists for {month}/{year}.'}
                )

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)

        spent_lookup = self.context.get('spent_lookup')
        if spent_lookup is not None:
            spent = spent_lookup.get((instance.category, instance.month, instance.year))
        else:
            spent = get_spent_for_budget(instance)

        data.update(calculate_budget_usage(instance.amount, spent, instance.alert_thresholds))
        return data
