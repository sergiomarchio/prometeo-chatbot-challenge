from abc import abstractmethod
from collections import defaultdict
from django.utils.translation import gettext as _
from requests import Response

from chatbot import settings

import requests
from urllib.parse import urljoin


class Api:
    base_url = getattr(settings, "CONFIG")['base_url'] + "/"
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
            self._response = requests.get(self.url, headers=self.headers)

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
        pass

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

    def is_ok(self):
        return (200 <= self.response.status_code < 300
                and self.response_json['status'] == "success"
                and "providers" in self.response_json)

    def digest_message(self) -> str:
        if not self.response:
            raise ReferenceError(_("Oh no! Something went wrong!"))

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

    def __init__(self, api_key, code):
        super().__init__(api_key, code)

    def is_ok(self) -> bool:
        return (200 <= self.response.status_code < 300
                and self.response_json['status'] == "success")

    def digest_message(self) -> str:
        return "---" + str(self.__dict__)

