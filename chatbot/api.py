from abc import abstractmethod
from collections import defaultdict
from django.utils.translation import gettext as _
from enum import Enum
import requests
from requests import Response
from urllib.parse import urljoin

from chatbot import settings


class Method(Enum):
    GET = "GET"
    POST = "POST"


class Api:
    base_url = getattr(settings, "CONFIG")['base_url'] + "/"
    method = None
    parameters = ""

    def __init__(self, api_key, *path_params, **query_params):
        self.headers = {
            'X-API-Key': api_key
        }
        self.path_params = path_params
        self.query_params = query_params
        self._url = None
        self._response = None
        self._response_json = None

    @property
    def url(self):
        if not self._url:
            self._url = urljoin(self.base_url, self.parameters.format(*self.path_params))

        print("url:", self._url)

        return self._url

    @property
    def response(self) -> Response:
        if not self._response:
            if self.method == Method.GET:
                self._response = requests.get(self.url, data=self.query_params, headers=self.headers)
            elif self.method == Method.POST:
                self._response = requests.post(self.url, data=self.query_params, headers=self.headers)
            else:
                raise NameError(f"Unsupported method: '{self.method}'")

        self.log_response()

        return self._response

    @property
    def response_json(self):
        if not self._response_json:
            self._response_json = self.response.json()

        return self._response_json

    @abstractmethod
    def is_ok(self) -> bool:
        """
        Checks if the API response was successful
        """
        pass

    @abstractmethod
    def digest_message(self) -> str:
        """
        Processes the response and returns the bot message
        """
        if not self.response:
            raise ReferenceError(_("Oh no! Something went wrong!"))

        return ""

    def log_response(self):
        print()
        print(self.url)
        print(self.headers)
        print()
        print(self._response.status_code)
        print()
        print(self._response.headers)
        print()
        print(self._response.content)
        print()


class Provider(Api):
    parameters = "provider/"
    method = Method.GET

    def is_ok(self):
        return (200 <= self.response.status_code < 300
                and self.response_json['status'] == "success"
                and "providers" in self.response_json)

    def digest_message(self) -> str:
        super().digest_message()

        banks_per_country = defaultdict(list)
        for bank in self.response_json['providers']:
            banks_per_country[bank['country']].append(bank['name'])

        bank_string = _("The available banks per country are:") + "\n"
        for country, banks in sorted(banks_per_country.items()):
            bank_links = [f'<a class="message-link">{bank}</a>' for bank in banks]

            bank_string += country + ":\n" + "\n".join(bank_links) + "\n\n"

        return bank_string


class ProviderLoginParameters(Api):
    parameters = "provider/{}/"
    method = Method.GET

    def is_ok(self) -> bool:
        return (200 <= self.response.status_code < 300
                and self.response_json['status'] == "success")

    def digest_message(self) -> str:
        super().digest_message()

        return f"Logging into {self.response_json['provider']['bank']['name']}..."


class Login(Api):
    parameters = "login/"
    method = Method.POST

    def __init__(self, api_key, *path_params, **query_params):
        super().__init__(api_key, *path_params, **query_params)
        self.headers["accept"] = "application/json"
        self.headers["content-type"] = "application/x-www-form-urlencoded"

    def is_ok(self):
        return (self.response.status_code == 200
                and self.response_json['status'] == "logged_in"
                and 'key' in self.response_json)

    def digest_message(self) -> str:
        super().digest_message()

        return self.response_json['status']
