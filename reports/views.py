from datetime import datetime, timedelta
from django.utils import timezone

from django.shortcuts import render

from django.views.generic import View
from django.template.response import TemplateResponse
from django.http.response import HttpResponseBadRequest

from django.conf import settings

import tb
import json
from websocket import create_connection


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
    
    def connect_websocket(self, token, entityId, startTs, endTs):
        ws = create_connection("ws://platform.canionlabs.io:9090/api/ws/plugins/telemetry?token="+token)
        
        object_send = {
            'historyCmds': [
              {
                  'cmdId': 1,
                  'entityType': "DEVICE",
                  'entityId': entityId,
                  'keys': "t0,t1,h0,h1",
                  'startTs': startTs,
                  'endTs': endTs
              }
            ]
        }
        data = json.dumps(object_send)
        ws.send(data)

        result = ws.recv()
        ws.close()
        
        return result

    def get(self, request, *args, **kwargs):

        selected_date = request.GET.get("date", timezone.now())
        try:
            fmt_date = self._datetime_handler(selected_date)
        except ValueError as e:
            return HttpResponseBadRequest("Invalid date format")

        device_id = kwargs["device_id"]
        tb_context = self.request_token()
        starts, ends = self._get_starts_ends_timestamps(fmt_date)

        result_ws = self.connect_websocket(tb_context["token"], device_id, int(starts)*1000, int(ends)*1000)
        print(f'RESULTADO: {result_ws}')

        return TemplateResponse(
            request, 'reports/daily_report.html'
        )
