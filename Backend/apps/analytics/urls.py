from django.urls import path

from .views import AnalyticsView, DashboardView

dashboard_urlpatterns = [path('', DashboardView.as_view(), name='dashboard')]
analytics_urlpatterns = [path('', AnalyticsView.as_view(), name='analytics')]
