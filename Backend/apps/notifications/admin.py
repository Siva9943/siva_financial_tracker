from django.contrib import admin

from .models import Notification, Reminder


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('user', 'reminder_type', 'description', 'reminder_date', 'is_completed')
    list_filter = ('reminder_type', 'is_completed', 'recurrence')
    search_fields = ('description', 'user__username')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('title', 'message', 'user__username')
