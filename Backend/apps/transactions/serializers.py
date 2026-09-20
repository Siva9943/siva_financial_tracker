from rest_framework import serializers

from .models import RecurringTransaction, Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            'id',
            'transaction_type',
            'amount',
            'category',
            'description',
            'transaction_date',
            'payment_method',
            'reference',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value

    def validate_category(self, value):
        if not value.strip():
            raise serializers.ValidationError('Category is required.')
        return value


class TypeLockedTransactionSerializer(TransactionSerializer):
    """Base for Income/Expense serializers where transaction_type is fixed by the endpoint."""

    class Meta(TransactionSerializer.Meta):
        read_only_fields = TransactionSerializer.Meta.read_only_fields + ('transaction_type',)


class IncomeSerializer(TypeLockedTransactionSerializer):
    pass


class ExpenseSerializer(TypeLockedTransactionSerializer):
    pass


class RecurringTransactionSerializer(serializers.ModelSerializer):
    next_run_date = serializers.DateField(required=False)

    class Meta:
        model = RecurringTransaction
        fields = (
            'id',
            'transaction_type',
            'amount',
            'category',
            'description',
            'payment_method',
            'frequency',
            'start_date',
            'next_run_date',
            'end_date',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value

    def validate(self, attrs):
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if end_date and start_date and end_date <= start_date:
            raise serializers.ValidationError({'end_date': 'End date must be after the start date.'})
        return attrs

    def create(self, validated_data):
        validated_data.setdefault('next_run_date', validated_data['start_date'])
        return super().create(validated_data)
