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


class Provider(Api):
    parameters = "provider/"

    def __init__(self, api_key):
        super().__init__(api_key)

    def get(self):
        print(self.url())
        print(self.headers)
        response = requests.get(self.url(), headers=self.headers)
        print(response.status_code)
        print(response.headers)
        print(response.content)

        return response
