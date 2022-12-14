from abc import abstractmethod
from django.utils.translation import gettext as _
from enum import Enum
import requests
from requests import Response
from urllib.parse import urljoin

from chatbot import settings


class Method(Enum):
    GET = "GET"
    POST = "POST"


class ApiException(Exception):
    def __init__(self, message="", status=500):
        super().__init__(message)

        self.message = message
        self.status = status


class Api:
    base_url = getattr(settings, "CONFIG")['base_url'] + "/"
    method = None
    parameters = ""

    def __init__(self, api_key, path_params=None, query_params=None, data=None):
        self.headers = {
            'X-API-Key': api_key
        }
        self.path_params = {} if path_params is None else path_params
        self.query_params = {} if query_params is None else query_params
        self.data = data

        self._url = None
        self._response = None
        self._response_json = None

    @property
    def url(self):
        if not self._url:
            print(self.parameters)
            print(self.path_params)
            self._url = urljoin(self.base_url, self.parameters.format(**self.path_params))

        print("url:", self._url)

        return self._url

    @property
    def response(self) -> Response:
        if not self._response:
            print()
            print("data:", self.data)
            print("query:", self.query_params)

            if self.method == Method.GET:
                self._response = requests.get(self.url, params=self.query_params, headers=self.headers)
            elif self.method == Method.POST:
                self._response = requests.post(self.url, params=self.query_params, data=self.data, headers=self.headers)
            else:
                raise NameError(f"Unsupported method: '{self.method}'")

            self._log_response()

        return self._response

    @property
    def response_json(self):
        if not self._response_json:
            self._response_json = self.response.json()

        return self._response_json

    @abstractmethod
    def is_ok(self) -> bool:
        """
        Checks if the API response was successful,
        based on the contract in the API documentation
        """
        pass

    def successful_json(self):
        """
        Checks if the API was successful or not, raising ApiException if not.
        @return
        json response
        """
        if not self.response or not self.response_json:
            raise ApiException(_("Something went wrong!"))

        if self.response_json.get('message') == 'Key not Found':
            raise ApiException(_("There was an error with the API key, please start again..."))

        if not self.is_ok():
            raise ApiException(_("Something went wrong... Please try again later..."))

        return self.response_json

    def _log_response(self):
        print()
        print("URL:", self.url)
        print("headers:", self.headers)
        print()
        print("response status code:", self._response.status_code)
        print("response headers:", self._response.headers)
        print("response content:", self._response.content)
        print()
