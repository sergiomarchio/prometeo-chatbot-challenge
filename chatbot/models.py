from django import forms
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
import re
from typing import Optional
import unicodedata

from . import api
from . import settings
from .forms import ProviderLoginForm
from .utils import Dictionarizable


class ApiKey:
    @staticmethod
    def guest_key():
        return getattr(settings, "API_KEY")


class Message(Dictionarizable):
    def __init__(self, sender, content):
        self.sender = sender
        self.content = content

    def dict(self) -> dict:
        """
        @return
        dictionary with the contents of the message
        """
        return {
            'message': {
                'sender': self.sender,
                'content': self.content
            }
        }

    def json_response(self, status):
        """
        Converts the message into a JsonResponse object
        """
        return JsonResponse(self.dict(), status=status)


class BotMessage(Message):
    def __init__(self, content):
        super().__init__("bot", content)


class UserMessage(Message):
    def __init__(self, content):
        super().__init__("user", content)


class ModalForm(Dictionarizable):

    def __init__(self, file: str, form: forms.Form, request, logo=None, name=None):
        self.file = file
        self.form = form
        self.request = request
        self.logo = logo
        self.name = name

    def dict(self):
        return {
            'modal-form': render_to_string(self.file, {
                'form': self.form.as_div(),
                'logo': self.logo,
                'name': self.name
            }, request=self.request)
        }


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

    def __init__(self, cache: dict, request):
        self.cache = cache
        self.api_key = cache['api-key']
        self.request = request

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

        return None

    def process_message(self, message) -> Dictionarizable:
        for provider in self.cache['providers']:
            if normalize_string(message) == normalize_string(provider['name']):
                provider_params = api.ProviderLoginParameters(self.api_key, {'code': provider['code']})
                self.cache['active_provider'] = provider_params.response_json

                provider = provider_params.response_json['provider']
                logo = provider['logo']

                provider_fields = [
                    {'name': x['name'],
                     'type': x['type'],
                     'placeholder': x['label_es'] if self.request.LANGUAGE_CODE == 'es' else x['label_en']
                     } for x in provider['auth_fields']
                    if not x['interactive'] and not x['optional']
                ]

                return ModalForm('chatbot/provider_login.html',
                                 ProviderLoginForm(provider_fields=provider_fields),
                                 self.request,
                                 logo=logo,
                                 name=provider['bank']['name'])

        api_object = self.parse_message(message)
        if not api_object:
            return BotMessage(_("Sorry, could you give me more details about what you want to do?"))

        json_response = api_object.response_json

        if 'message' in json_response and json_response['message'] == 'Key not Found':
            raise Exception(_("There was an error with the API key, please log in again..."))

        if not api_object.is_ok():
            raise Exception(_("Oops! Something went wrong, please try again..."))

        return BotMessage(api_object.digest_message())


class MessageResponse(JsonResponse):
    def __init__(self, content, status, **kwargs):
        kwargs.setdefault('status', status)
        super().__init__(BotMessage(content).dict(), **kwargs)


class ErrorResponse(MessageResponse):
    def __init__(self, content=None, status=500, **kwargs):
        if content is None:
            content = _("Beep-bop! Something went wrong... Please try again later...")

        super().__init__(content, status, **kwargs)
