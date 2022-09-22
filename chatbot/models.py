from collections import defaultdict
from django import forms
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
import re
from typing import Optional
import unicodedata

from .api import api, auth
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

    def process_message(self, message) -> Dictionarizable:
        """
        Parses the message looking for fixed strings or patterns, and calls the corresponding action
        @return
        the result of that action (it could be a message, a modal, ...)
        """
        normalized_message = normalize_string(message)

        # Check for exact provider names for login
        for provider in self.cache['providers']:
            if normalized_message == normalize_string(provider['name']):
                return self.action_login(provider['code'])

        # Useful regex common patterns
        any_before = r"^(.* +)?"
        any_after = r"( +.*)?$"

        if re.match(any_before + _("log *out") + any_after, normalized_message):
            return self.action_logout()

        if re.match(any_before + _("banks?") + any_after, normalized_message):
            return self.action_provider()

        if re.match(any_before + _("(hi)|(hello)") + any_after, normalized_message):
            return BotMessage(_("Hello! Nice to meet you :)"))

        return BotMessage(_("Sorry, could you give me more details about what you want to do?"))

    def action_provider(self) -> BotMessage:
        provider_response = api.Provider(self.api_key)
        provider_response.validate_response()

        provider_response = provider_response.response_json

        banks_per_country = defaultdict(list)
        for bank in provider_response['providers']:
            banks_per_country[bank['country']].append(bank['name'])

        bank_string = _("The available banks per country are:") + "\n"
        for country, banks in sorted(banks_per_country.items()):
            bank_links = [f'<a class="message-link">{bank}</a>' for bank in banks]

            bank_string += country + ":\n" + "\n".join(bank_links) + "\n\n"

        return BotMessage(bank_string)

    def action_login(self, provider_code) -> ModalForm:
        provider = api.ProviderLoginParameters(self.api_key, {'code': provider_code})
        provider.validate_response()
        provider_response = provider.response_json

        self.cache['active_provider'] = provider_response
        provider = provider_response['provider']
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

    def action_logout(self) -> BotMessage:
        if 'active_provider' not in self.cache:
            return BotMessage(_("It seems that you are not logged in..."))

        auth.Logout(self.api_key, self.cache['active_provider'].get('key')).validate_response()

        name = self.cache['active_provider']['provider']['bank']['name']
        del self.cache['active_provider']

        return BotMessage(_("Thank you for operating with ") + f"{name}")


class MessageResponse(JsonResponse):
    def __init__(self, content, status, **kwargs):
        kwargs.setdefault('status', status)
        super().__init__(BotMessage(content).dict(), **kwargs)


class ErrorResponse(MessageResponse):
    def __init__(self, content=None, status=500, **kwargs):
        if content is None:
            content = _("Beep-bop! Something went wrong... Please try again later...")

        super().__init__(content, status, **kwargs)
