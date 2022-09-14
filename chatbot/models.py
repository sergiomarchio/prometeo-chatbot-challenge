import re

from collections import defaultdict
from django.utils.translation import gettext as _

from . import api
from . import settings


class ApiKey:
    @staticmethod
    def guest_key():
        return getattr(settings, "API_KEY")


class Message:
    def __init__(self, sender, content):
        self.sender = sender
        self.content = content


class BotMessage(Message):
    def __init__(self, content):
        super().__init__("bot", content)


class UserMessage(Message):
    def __init__(self, content):
        super().__init__("user", content)


class MessageHistory:

    def __init__(self):
        self.message_history = []

    def __str__(self):
        return [msg for msg in self.messages()].__str__()

    def add(self, message: Message):
        self.message_history.append(message)

    def messages(self):
        for message in self.message_history:
            yield {"sender": message.sender, "content": message.content}


class MessageProcessor:

    def __init__(self, api_key):
        self.api_key = api_key

    def process_message(self, message):
        if re.match(_("banks?"), message):
            response = api.Provider(self.api_key).get()

            if not 200 <= response.status_code < 300 or response.json()['status'] != 'success':
                return _("There was an issue, please try again...")

            banks_per_country = defaultdict(list)
            for bank in response.json()['providers']:
                banks_per_country[bank['country']].append(bank['name'])

            bank_string = _("The available banks per country are:") + "\n"
            for country, banks in sorted(banks_per_country.items()):
                bank_string += country + ":\n" + "\n".join(banks) + "\n\n"

            return bank_string

        return "ok"
