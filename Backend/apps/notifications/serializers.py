from rest_framework import serializers

from .models import Notification, Reminder


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = (
            'id',
            'reminder_type',
            'description',
            'amount',
            'reminder_date',
            'recurrence',
            'is_completed',
            'snoozed_until',
            'last_notified_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'is_completed', 'snoozed_until', 'last_notified_at', 'created_at', 'updated_at')

    def validate_amount(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value

    def validate_description(self, value):
        if not value.strip():
            raise serializers.ValidationError('Description is required.')
        return value


class SnoozeReminderSerializer(serializers.Serializer):
    snoozed_until = serializers.DateField()

    def validate_snoozed_until(self, value):
        from datetime import date

        if value < date.today():
            raise serializers.ValidationError('Cannot snooze to a date in the past.')
        return value


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'notification_type', 'title', 'message', 'is_read', 'created_at')
        read_only_fields = fields
