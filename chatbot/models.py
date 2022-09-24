from collections import defaultdict
from django import forms
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
import re
import unicodedata

from .api import auth, meta, transactional
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

        # Sequential parsing of message
        actions = {
            _("log *out"): self.action_logout,
            _("customers?"): self.action_client,
            _("banks?"): self.action_provider,
            _("accounts?"): self.action_account,
            _("cards?"): self.action_card,
            _("(data)|(info)"): self.action_info,
            _("(hi)|(hello)"): lambda: BotMessage(_("Hello! Nice to meet you :)")),
        }

        for pattern, action in actions.items():
            if re.match(any_before + pattern + any_after, normalized_message):
                return action()

        return BotMessage(_("Sorry, could you give me more details about what you want to do?"))

    def action_provider(self) -> BotMessage:
        provider_response = meta.Provider(self.api_key)
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
        provider = meta.ProviderDetail(self.api_key, provider_code=provider_code)
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

    def action_client(self) -> BotMessage:
        if 'active_provider' not in self.cache:
            return BotMessage(_("It seems that you are not logged in..."))

        client_api = auth.Client(self.api_key, self.cache['active_provider'].get('key'))
        client_api.validate_response()
        client_response = client_api.response_json

        clients = client_response['clients']
        self.cache['active_provider']['clients'] = clients

        if len(clients) == 0:
            return BotMessage(_("There are no registered customers for this user"))

        client_names = [client for client in clients.values()]

        return BotMessage(client_names)

    def action_info(self):
        if 'active_provider' not in self.cache:
            return BotMessage(_("It seems that you are not logged in..."))

        info_api = transactional.Info(self.api_key, self.cache['active_provider'].get('key'))
        info_api.validate_response()
        info_response = info_api.response_json

        info = info_response['info']

        message = (_('Your info') + ":\n"
                   + _('ID') + f": {info['document']}\n"
                   + _('Name') + f": {info['name']}\n"
                   + _('email') + f": {info['email']}")

        return BotMessage(message)

    def action_account(self):
        if 'active_provider' not in self.cache:
            return BotMessage(_("It seems that you are not logged in..."))

        account_api = transactional.Account(self.api_key, self.cache['active_provider'].get('key'))
        account_api.validate_response()
        account_response = account_api.response_json

        accounts = account_response['accounts']
        self.cache['active_provider']['accounts'] = accounts

        # This is for translation purposes, so django can generate the .po with this strings
        translation_names = (_('balance') + _('branch') + _('currency')
                             + _('id') + _('name') + _('number'))

        message_parts = []
        for account in accounts:
            rows = [f'<div name="{key}" class="item row">'
                    '<div class="key">' + _(key) + ':</div>'
                    f'<div class="value">{value}</div>'
                    f'</div>' for key, value in account.items() if key != 'id']

            message_parts += [f'<div class="item link" name=\"{account["id"]}\">' + "\n".join(rows) + '</div>']

        return BotMessage("\n".join(message_parts))

    def action_card(self):
        if 'active_provider' not in self.cache:
            return BotMessage(_("It seems that you are not logged in..."))

        card_api = transactional.Card(self.api_key, self.cache['active_provider'].get('key'))
        card_api.validate_response()
        card_response = card_api.response_json

        cards = card_response['credit_cards']
        self.cache['active_provider']['cards'] = cards

        # This is for translation purposes, so django can generate the .po with this strings
        translation_names = (_('balance_dollar') + _('balance_local') + _('close_date')
                             + _('due_date') + _('id') + _('name') + _('number'))

        message_parts = []
        for card in cards:
            rows = [f'<div name="{key}" class="item row">'
                    '<div class="key">' + _(key) + ':</div>'
                    f'<div class="value">{value}</div>'
                    f'</div>' for key, value in card.items() if key != 'id']

            message_parts += [f'<div class="item link" name=\"{card["id"]}\">' + "\n".join(rows) + '</div>']

        return BotMessage("\n".join(message_parts))


class ErrorResponse(JsonResponse):
    def __init__(self, content=None, **kwargs):
        kwargs.setdefault('status', 500)
        if content is None:
            content = _("Beep-bop! Something went wrong... Please try again later...")

        super().__init__(BotMessage(content).dict(), **kwargs)
