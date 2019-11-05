import datetime

from django.shortcuts import render
from django.utils import timezone

from django.views.generic import View
from django.http.response import HttpResponse

import tb


class DailyReportView(View):
    def _get_starts_ends_timestamps(date):
        start = 
        end = date
        return start, end

    def _tb_handler(self, device_id, selected_date):
        starts, ends = self._get_starts_ends_timestamps(selected_date)
        platform = tb.TB()
        return platform.timeseries(entity_id=device_id)

    def get(self, *args, **kwargs):
        selected_date = self.request.GET.get("date", timezone.now())
        device_id = kwargs["device_id"]
        tb_context = self._tb_handler(device_id, selected_date)
        return render('monar_tbreports/templates/reports/daily_report.html')
