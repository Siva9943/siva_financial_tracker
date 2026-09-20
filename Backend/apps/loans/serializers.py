from decimal import Decimal

from rest_framework import serializers

from apps.transactions.models import Transaction

from .models import Loan, LoanPayment


class LoanCalculatorSerializer(serializers.Serializer):
    original_principal = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))
    annual_interest_rate = serializers.DecimalField(max_digits=6, decimal_places=3, min_value=0)
    interest_calculation_method = serializers.ChoiceField(choices=Loan.InterestMethod.choices)
    payment_frequency = serializers.ChoiceField(choices=Loan.PaymentFrequency.choices, default=Loan.PaymentFrequency.MONTHLY)
    start_date = serializers.DateField()
    maturity_date = serializers.DateField()
    emi_amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'), required=False)

    def validate(self, attrs):
        if attrs['maturity_date'] <= attrs['start_date']:
            raise serializers.ValidationError({'maturity_date': 'Maturity date must be after the start date.'})
        return attrs


def _default_extra_payment_scenarios():
    return [Decimal('0'), Decimal('1000'), Decimal('2000'), Decimal('5000'), Decimal('10000')]


class LoanSimulatorSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField(required=False)

    original_principal = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'), required=False)
    annual_interest_rate = serializers.DecimalField(max_digits=6, decimal_places=3, min_value=0, required=False)
    interest_calculation_method = serializers.ChoiceField(choices=Loan.InterestMethod.choices, required=False)
    payment_frequency = serializers.ChoiceField(choices=Loan.PaymentFrequency.choices, required=False)
    start_date = serializers.DateField(required=False)
    maturity_date = serializers.DateField(required=False)
    emi_amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'), required=False)

    extra_payment_scenarios = serializers.ListField(
        child=serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0),
        default=_default_extra_payment_scenarios,
    )

    def validate(self, attrs):
        if 'loan_id' in attrs:
            return attrs

        required_fields = (
            'original_principal', 'annual_interest_rate', 'interest_calculation_method',
            'payment_frequency', 'start_date', 'maturity_date',
        )
        missing = [field for field in required_fields if field not in attrs]
        if missing:
            raise serializers.ValidationError(
                {'loan_id': f'Provide a loan_id, or all of: {", ".join(missing)}.'}
            )

        if attrs['maturity_date'] <= attrs['start_date']:
            raise serializers.ValidationError({'maturity_date': 'Maturity date must be after the start date.'})

        return attrs


class LoanSerializer(serializers.ModelSerializer):
    outstanding_principal = serializers.DecimalField(max_digits=14, decimal_places=2, required=False)
    next_due_date = serializers.DateField(required=False)

    class Meta:
        model = Loan
        fields = (
            'id',
            'loan_name',
            'loan_type',
            'lender',
            'original_principal',
            'outstanding_principal',
            'annual_interest_rate',
            'interest_calculation_method',
            'emi_amount',
            'payment_frequency',
            'start_date',
            'maturity_date',
            'next_due_date',
            'processing_fee',
            'late_fee',
            'prepayment_penalty',
            'status',
            'notes',
            'priority_order',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_original_principal(self, value):
        if value <= 0:
            raise serializers.ValidationError('Original principal must be greater than zero.')
        return value

    def validate_annual_interest_rate(self, value):
        if value < 0:
            raise serializers.ValidationError('Interest rate cannot be negative.')
        return value

    def validate_emi_amount(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('EMI amount must be greater than zero.')
        return value

    def validate(self, attrs):
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        maturity_date = attrs.get('maturity_date', getattr(self.instance, 'maturity_date', None))
        if start_date and maturity_date and maturity_date <= start_date:
            raise serializers.ValidationError({'maturity_date': 'Maturity date must be after the start date.'})

        original_principal = attrs.get('original_principal', getattr(self.instance, 'original_principal', None))
        outstanding_principal = attrs.get('outstanding_principal')
        if outstanding_principal is not None and original_principal is not None:
            if outstanding_principal > original_principal:
                raise serializers.ValidationError(
                    {'outstanding_principal': 'Outstanding principal cannot exceed the original principal.'}
                )

        return attrs


class LoanPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanPayment
        fields = (
            'id',
            'payment_date',
            'amount',
            'principal_component',
            'interest_component',
            'late_fee',
            'extra_payment',
            'remaining_principal',
            'transaction_reference',
            'notes',
            'created_at',
        )
        read_only_fields = fields


class LoanReorderSerializer(serializers.Serializer):
    loan_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class LoanPaymentCreateSerializer(serializers.Serializer):
    payment_date = serializers.DateField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))
    late_fee = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=False, allow_null=True)
    payment_method = serializers.ChoiceField(choices=Transaction.PaymentMethod.choices, default=Transaction.PaymentMethod.OTHER)
    transaction_reference = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    notes = serializers.CharField(required=False, allow_blank=True, default='')
