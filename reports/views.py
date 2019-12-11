from datetime import datetime, timedelta
from django.utils import timezone

from django.shortcuts import render

from django.views.generic import View
from django.template.response import TemplateResponse
from django.http.response import HttpResponseBadRequest

from django.conf import settings

import tb


class DailyReportView(View):
    def _get_starts_ends_timestamps(self, date):
        starts = date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        ends = starts + timedelta(days=1)
        return starts.timestamp(), ends.timestamp()

    def _datetime_handler(self, date):
        if isinstance(date, datetime):
            return date
        return datetime.strptime(date, "%d/%m/%Y")

    def request_token(self):
        platform = tb.TB()
        return platform.login()

    def get(self, request, *args, **kwargs):

        device_id = kwargs["device_id"]
        selected_date = request.GET.get("date", timezone.now())
        try:
            fmt_date = self._datetime_handler(selected_date)
        except ValueError as e:
            return HttpResponseBadRequest("Invalid date format")

        tb_context = self.request_token()
        starts, ends = self._get_starts_ends_timestamps(fmt_date)

        data = {
            'tb_context': tb_context["token"],
            'device_id': device_id,
            'startTs': int(starts)*1000,
            'endTs': int(ends)*1000
        }

        return TemplateResponse(
            request, 'reports/daily_report.html', data
        )
