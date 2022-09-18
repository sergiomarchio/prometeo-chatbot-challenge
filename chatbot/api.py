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

    def __init__(self, api_key):
        self.headers = {
            'X-API-Key': api_key
        }

    def url(self):
        return urljoin(self.base_url, self.parameters)

    @abstractmethod
    def call(self) -> Response:
        pass

    @abstractmethod
    def digest_message(self) -> str:
        """
        Processes the response and returns the bot message
        """
        pass


class Provider(Api):
    parameters = "provider/"

    def __init__(self, api_key):
        super().__init__(api_key)
        self.response = None

    def call(self):
        print()
        print(self.url())
        print(self.headers)
        print()

        self.response = requests.get(self.url(), headers=self.headers)

        print(self.response.status_code)
        print()
        print(self.response.headers)
        print()
        print(self.response.content)
        print()

        return self.response

    def digest_message(self) -> str:
        if not self.response:
            raise ReferenceError(_("Oh no! Something went wrong!"))

        banks_per_country = defaultdict(list)
        for bank in self.response.json()['providers']:
            banks_per_country[bank['country']].append(bank['name'])

        bank_string = _("The available banks per country are:") + "\n"
        for country, banks in sorted(banks_per_country.items()):
            bank_links = [f'<a class="message-link">{bank}</a>' for bank in banks]

            bank_string += country + ":\n" + "\n".join(bank_links) + "\n\n"

        return bank_string
