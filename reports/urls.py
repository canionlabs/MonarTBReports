from django.urls import path

from .views import DailyReportView


app_name = "reports"

urlpatterns = [
    path("", DailyReportView.as_view(), name="daily-report"),
]
