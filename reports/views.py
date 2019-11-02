from django.shortcuts import render

from django.views.generic import View
from django.http.response import HttpResponse


class DailyReportView(View):
    def get(self, *args, **kwargs):
        device_id = kwargs["device_id"]
        return HttpResponse(f"{device_id}")
