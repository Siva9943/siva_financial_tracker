from django.urls import path

from .views import ReportView

report_urlpatterns = [path('<str:report_type>/', ReportView.as_view(), name='report')]
