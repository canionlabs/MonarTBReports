from datetime import datetime, timedelta

from django.shortcuts import render
from django.utils import timezone

from django.views.generic import View
from django.http.response import HttpResponseBadRequest
from django.template.response import TemplateResponse

import tb


class DailyReportView(View):
    def _get_starts_ends_timestamps(self, date):
        starts = date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        ends = starts + timedelta(days=1)
        return starts.timestamp(), ends.timestamp()

    def _tb_handler(self, device_id, selected_date):
        starts, ends = self._get_starts_ends_timestamps(selected_date)
        platform = tb.TB()
        return platform.timeseries(
            entity_id=device_id, starts=starts, ends=ends
        )

    def _datetime_handler(self, date):
        if isinstance(date, datetime):
            return date
        return datetime.strptime(date, "%d/%m/%Y")

    def get(self, request, *args, **kwargs):
        selected_date = request.GET.get("date", timezone.now())
        try:
            fmt_date = self._datetime_handler(selected_date)
        except ValueError as e:
            return HttpResponseBadRequest("Invalid date format")

        device_id = kwargs["device_id"]
        tb_context = self._tb_handler(device_id, fmt_date)
        from pprint import pprint
        pprint(tb_context)
        return TemplateResponse(
            request, 'reports/daily_report.html', tb_context
        )
