import re
from typing import Optional

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

    def parse_message(self, message) -> Optional[api.Api]:
        """
        Parse a message returning the object that corresponds
        to the API that must be called
        """

        if re.match(_("banks?"), message, re.IGNORECASE):
            return api.Provider(self.api_key)
        else:
            return None

    def process_message(self, message):
        api_object = self.parse_message(message)
        if api_object is None:
            return _("Sorry, could you give me more details about what you want to do?")

        response = api_object.call()
        json_response = response.json()

        if 'message' in json_response and json_response['message'] == 'Key not Found':
            raise ValueError(_("There was an error with the API key, please log in again..."))

        if not 200 <= response.status_code < 300 or json_response['status'] != 'success':
            return _("There was an issue, please try again...")

        return api_object.digest_message()
