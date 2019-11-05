import time
from urllib.parse import urlencode

import requests

from django.conf import settings


class TB:
    URL = settings.TB_URL
    USERNAME = settings.TB_USERNAME
    PASSWORD = settings.TB_PASSWORD

    def __init__(self):
        self.session = requests.Session()
        self.login()

    @staticmethod
    def _response_handler(status_code, response):
        if status_code != response.status_code:
            raise Exception("Erro tal")

    def _update_headers(self, new_header: dict):
        self.session.headers.update(new_header)

    def login(self):
        auth_url = f"{self.URL}/api/auth/login"
        response = self.session.post(auth_url, json={
            "username": self.USERNAME,
            "password": self.PASSWORD,
        })
        self._response_handler(200, response)

        auth_data = response.json()
        self._update_headers({
            "X-Authorization": f"Bearer {auth_data['token']}"
        })

    def timeseries(
        self, entity_id, starts, ends,
        entity_type="DEVICE", interval=None, agg=None, limit=None
    ):
        """
        Available params (API Side)
        ---------------------------
        keys: comma separated list of telemetry keys to fetch.
        startTs: unix timestamp that identifies start of the interval in milliseconds.
        endTs: unix timestamp that identifies end of the interval in milliseconds.
        interval: the aggregation interval, in milliseconds.
        agg: the aggregation function. One of MIN, MAX, AVG, SUM, COUNT, NONE.
        limit: the max amount of data points to return or intervals to process.
        """
        base_querystring = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "starts": starts,
            "ends": ends,
            "interval": interval,
            "agg": agg,
            "limit": limit,
        }

        params_querystring = {
            key: value
            for key, value in base_querystring.items()
            if value is not None
        }

        querystring = urlencode(params_querystring)
        timeseries_url = (
            f"{self.URL}/api/"
            f"plugins/telemetry/{entity_type}/{entity_id}/values/timeseries"
            f"?{querystring}"
        )
        response = self.session.get(timeseries_url)
        self._response_handler(200, response)
        return response.json()
