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


class DailyReportView(View):
    def _get_starts_ends_timestamps(self, date):
        starts = date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        ends = starts + timedelta(days=1)
        return starts.timestamp(), ends.timestamp()

    def _get_month_bondaries(self, date):
        starts = date.replace(day=1)
        ends = starts.replace(month=starts.month + 1)
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
                  'keys': "t0,t1,t2",
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

    def _get_temperature_list(self, response):
        all_values = []

        for device_response in response.values():
            all_values.extend([item for item in device_response])

        return all_values  # [ [timestamp, temperature] ]

    def _get_temperature_bondaries(self, temperature_list):
        temperature_values = [value[1] for value in temperature_list]
        return min(temperature_list), max(temperature_list)

    def _slice_period(self, temperature_list, day_date, start_hour, end_hour):
        start_timestamp = day_date.replace(hour=start_hour).timestamp() * 1000
        end_timestamp = day_date.replace(hour=end_hour).timestamp() * 1000

        period_filter = filter(
            lambda item: item[0] >= start_timestamp and item[0] < end_timestamp,
            temperature_list
        )

        dd = []
        for item in temperature_list:
            if item[0] >= start_timestamp and item[0] < end_timestamp:
                dd.append(item)
        # print(start_timestamp)
        # print(end_timestamp)
        # print(list(period_filter) == temperature_list)
        print(dd)

        # return [item[1] for item in period_filter]
        return dd


    def get(self, request, *args, **kwargs):
        context = {}

        selected_date = request.GET.get("date", timezone.now())
        try:
            fmt_date = self._datetime_handler(selected_date)
        except ValueError as e:
            return HttpResponseBadRequest("Invalid date format")

        device_id = kwargs["device_id"]
        tb_context = self.request_token()["token"]

        starts, ends = self._get_month_bondaries(fmt_date)
        print(starts)
        print(ends)
        result_ws = json.loads(self.connect_websocket(
            tb_context,
            device_id, 
            int(starts)*1000, 
            int(ends)*1000)
        )

        monthly_data = self._get_temperature_list(result_ws["data"])
        print(calendar.monthrange(fmt_date.year, fmt_date.month))
        days_on_month = calendar.monthrange(fmt_date.year, fmt_date.month)[1]
        for day in range(1, days_on_month + 1):
            day_date = fmt_date.replace(day=day)
            print(day_date)
            period_1_temp_list = self._slice_period(monthly_data, day_date, start_hour=8, end_hour=16)
            period_2_temp_list = self._slice_period(monthly_data, day_date, start_hour=16, end_hour=0)
            period_3_temp_list = self._slice_period(monthly_data, day_date, start_hour=0, end_hour=8)

            context.update({
                day: {
                    "period_1": {
                        "mon": period_1_temp_list[0] if period_1_temp_list else None,
                        "min": min([item[1] for item in period_1_temp_list]) if period_1_temp_list else None,
                        "max": max([item[1] for item in period_1_temp_list]) if period_1_temp_list else None,
                    },
                    "period_2": {
                        "mon": period_2_temp_list[0] if period_2_temp_list else None,
                        "min": min([item[1] for item in period_2_temp_list]) if period_2_temp_list else None,
                        "max": max([item[1] for item in period_2_temp_list]) if period_2_temp_list else None,
                    },
                    "period_3": {
                        "mon": period_3_temp_list[0] if period_3_temp_list else None,
                        "min": min([item[1] for item in period_3_temp_list]) if period_3_temp_list else None,
                        "max": max([item[1] for item in period_3_temp_list]) if period_3_temp_list else None,
                    },
                }
            })

        import pprint
        pprint.pprint(context)

        return TemplateResponse(
            request, 'reports/daily_report.html', context
        )
    #http://localhost:8000/reports/13ddf920-ff7d-11e9-8ad7-1d31d20907a4/daily/?date=29/11/2019
