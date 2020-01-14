from datetime import datetime, timedelta
import calendar
import json

from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.template.response import TemplateResponse
from django.http.response import HttpResponseBadRequest
from django.conf import settings

from websocket import create_connection
import tb


class MonthlyReportView(View):
    def _get_month_bondaries(self, date):
        start_timestamp = date.replace(day=1)
        end_timestamp = start_timestamp.replace(month=start_timestamp.month + 1)
        return start_timestamp.timestamp(), end_timestamp.timestamp()

    def _datetime_handler(self, date):
        if isinstance(date, datetime):
            return date
        return datetime.strptime(date, "%d/%m/%Y")

    def request_token(self):
        platform = tb.TB()
        return platform.login()
    
    def connect_websocket(self, token, entityId, startTs, endTs):
        websocket_connection = create_connection("ws://platform.canionlabs.io:9090/api/ws/plugins/telemetry?token="+token)

        object_send = {
            'tsSubCmds': [],
            'historyCmds': [
                {
                    'cmdId': 1,
                    'entityType': "DEVICE",
                    'entityId': entityId,
                    'keys': "t0,t1,t2",
                    'startTs': startTs,
                    'endTs': endTs,
                    'interval':7200000,
                    'limit':144,
                    'agg':"AVG"
                }
            ],
            'attrSubCmds': []
        }
        data = json.dumps(object_send)
        websocket_connection.send(data)

        result = websocket_connection.recv()
        websocket_connection.close()

        return result

    def _get_temperature_list(self, response):
        all_values = []

        for device_response in response.values():
            all_values.extend([item for item in device_response])

        return all_values  # [ [timestamp, temperature] ]

    def _slice_period(self, temperature_list, day_date, start_hour, end_hour, minute_end):
        start_timestamp = int(day_date.replace(hour=start_hour).timestamp()) * 1000
        end_timestamp = int(day_date.replace(hour=end_hour, minute=minute_end).timestamp()) * 1000

        items_sliced = []
        for item in temperature_list:
            if item[0] >= start_timestamp and item[0] <= end_timestamp:
                items_sliced.append(item)

        return items_sliced

    def update_response(self ,day, period_1_temp_list, period_2_temp_list, period_3_temp_list,response):

        response.update({
                day: {
                    "period_1": {
                        "mon": period_1_temp_list[0] if period_1_temp_list else None,
                        "min": min([item[1] for item in period_1_temp_list]) if period_1_temp_list else "-",
                        "max": max([item[1] for item in period_1_temp_list]) if period_1_temp_list else "-",
                    },
                    "period_2": {
                        "mon": period_2_temp_list[0] if period_2_temp_list else None,
                        "min": min([item[1] for item in period_2_temp_list]) if period_2_temp_list else "-",
                        "max": max([item[1] for item in period_2_temp_list]) if period_2_temp_list else "-",
                    },
                    "period_3": {
                        "mon": period_3_temp_list[0] if period_3_temp_list else None,
                        "min": min([item[1] for item in period_3_temp_list]) if period_3_temp_list else "-",
                        "max": max([item[1] for item in period_3_temp_list]) if period_3_temp_list else "-",
                    },
                }
            })

        return response


    def get(self, request, *args, **kwargs):
        response = {}

        selected_date = request.GET.get("date", timezone.now())
        try:
            fmt_date = self._datetime_handler(selected_date)
        except ValueError as e:
            return HttpResponseBadRequest("Invalid date format")

        device_id = kwargs["device_id"]
        thingsboard_context = self.request_token()["token"]

        starts, ends = self._get_month_bondaries(fmt_date)

        result_websocket = json.loads(self.connect_websocket(
            thingsboard_context,
            device_id, 
            int(starts)*1000, 
            int(ends)*1000
        ))

        monthly_data = self._get_temperature_list(result_websocket["data"])
        days_on_month = calendar.monthrange(fmt_date.year, fmt_date.month)[1]

        for day in range(1, days_on_month + 1):
            day_date = fmt_date.replace(day=day)
            period_1_temp_list = self._slice_period(monthly_data, day_date, start_hour=8, end_hour=15, minute_end=59)
            period_2_temp_list = self._slice_period(monthly_data, day_date, start_hour=16, end_hour=23, minute_end=59)
            period_3_temp_list = self._slice_period(monthly_data, day_date, start_hour=0, end_hour=7, minute_end=59)

            response = self.update_response(day, period_1_temp_list, period_2_temp_list, period_3_temp_list, response)

        context = {"response":response}

        return TemplateResponse(
            request, 'reports/daily_report.html', context
        )