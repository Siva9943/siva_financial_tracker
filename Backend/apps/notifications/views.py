from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import NotificationFilter, ReminderFilter
from .models import Notification, Reminder
from .serializers import NotificationSerializer, ReminderSerializer, SnoozeReminderSerializer


class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    filterset_class = ReminderFilter
    search_fields = ('description',)
    ordering_fields = ('reminder_date', 'created_at')

    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def snooze(self, request, pk=None):
        reminder = self.get_object()
        serializer = SnoozeReminderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reminder.snoozed_until = serializer.validated_data['snoozed_until']
        reminder.save(update_fields=['snoozed_until', 'updated_at'])
        return Response(ReminderSerializer(reminder).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        reminder = self.get_object()
        reminder.is_completed = True
        reminder.save(update_fields=['is_completed', 'updated_at'])
        return Response(ReminderSerializer(reminder).data)


class NotificationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter
    ordering_fields = ('created_at',)

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'success': True, 'message': f'{updated} notification(s) marked as read.'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        return Response({'success': True, 'count': self.get_queryset().filter(is_read=False).count()})
