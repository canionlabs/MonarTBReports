import requests

from django.conf import settings

from .exceptions import TBException


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
            raise TBException(
                f"Unexpected Response ({response.status_code}) \n"
                f"{response.content}"
            )

    def login(self):
        auth_url = f"{self.URL}/api/auth/login"
        response = self.session.post(auth_url, json={
            "username": self.USERNAME,
            "password": self.PASSWORD,
        })
        self._response_handler(200, response)

        return response.json()
