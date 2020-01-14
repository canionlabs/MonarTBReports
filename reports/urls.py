from django.urls import path

from .views import MonthlyReportView


app_name = "reports"

urlpatterns = [
    path("<str:device_id>/monthly/", MonthlyReportView.as_view(), name="monthly-report"),
]
