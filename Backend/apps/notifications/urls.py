from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet, ReminderViewSet

_reminder_router = DefaultRouter()
_reminder_router.register('', ReminderViewSet, basename='reminder')
reminder_urlpatterns = _reminder_router.urls

_notification_router = DefaultRouter()
_notification_router.register('', NotificationViewSet, basename='notification')
notification_urlpatterns = _notification_router.urls
