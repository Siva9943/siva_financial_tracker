import django_filters

from .models import Notification, Reminder


class ReminderFilter(django_filters.FilterSet):
    class Meta:
        model = Reminder
        fields = ('reminder_type', 'is_completed', 'recurrence')


class NotificationFilter(django_filters.FilterSet):
    class Meta:
        model = Notification
        fields = ('notification_type', 'is_read')
