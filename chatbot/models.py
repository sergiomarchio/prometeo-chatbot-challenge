from django.utils.translation import gettext as _
import re
from typing import Optional
import unicodedata

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

    def dict(self) -> dict:
        """
        @return
        dictionary with the contents of the message
        """
        return {
            "sender": self.sender,
            "content": self.content
        }


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


def normalize_string(string):
    return (unicodedata.normalize('NFD', string)
                          .encode('ascii', 'ignore').decode()
                          .lower())


class MessageProcessor:

    def __init__(self, cache: dict):
        self.cache = cache
        self.api_key = cache['api-key']

    def parse_message(self, message) -> Optional[api.Api]:
        """
        Parse a message returning the object that corresponds
        to the API that must be called
        """
        normalized_message = normalize_string(message)

        any_before = r"^(.* +)?"
        any_after = r"( +.*)?$"

        if re.match(any_before + _("banks?") + any_after, normalized_message):
            return api.Provider(self.api_key)

        for provider in self.cache['providers']:
            if normalized_message == normalize_string(provider['name']):
                return api.ProviderLoginParameters(self.api_key, provider['code'])

        return None

    def process_message(self, message):
        api_object = self.parse_message(message)
        if not api_object:
            return _("Sorry, could you give me more details about what you want to do?")

        json_response = api_object.response_json

        if 'message' in json_response and json_response['message'] == 'Key not Found':
            raise ValueError(_("There was an error with the API key, please log in again..."))

        if not api_object.is_ok():
            return _("There was an issue, please try again...")

        return api_object.digest_message()
