from collections import defaultdict

from django import forms
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
import re

from .api import auth, meta, transactional
from . import settings
from .forms import ProviderLoginForm
from .utils import Dictionarizable, DateProcessor, BotException, ActionSelector, normalize_string


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


class MessageProcessor:

    def __init__(self, cache: dict, request):
        self.cache = cache
        self.api_key = cache['api-key']
        self.request = request

    @property
    def provider_session(self):
        return self.cache.get('provider_session')

    @provider_session.setter
    def provider_session(self, provider_session):
        self.cache['provider_session'] = provider_session

    @provider_session.deleter
    def provider_session(self):
        del self.cache['provider_session']

    @property
    def session_accounts(self):
        self.require_logged_in()

        accounts = self.provider_session.get('accounts')
        if not accounts:
            accounts = transactional.Account(self.api_key, self.provider_session.get('key')
                                             ).successful_json()['accounts']

            self.provider_session['accounts'] = accounts

        return accounts

    @property
    def session_credit_cards(self):
        self.require_logged_in()

        cards = self.provider_session.get('credit_cards')
        if not cards:
            cards = transactional.CreditCard(self.api_key, self.provider_session.get('key')
                                             ).successful_json()['credit_cards']

            self.provider_session['credit_cards'] = cards

        return cards

    def is_user_logged_in(self):
        return self.provider_session and 'key' in self.provider_session
    
    def require_logged_in(self):
        if not self.is_user_logged_in():
            raise BotException(_("You must log in first!"))
        return True

    def require_not_logged_in(self):
        if self.is_user_logged_in():
            raise BotException(_('You are already logged in {provider}, '
                                 'please <a class="message-link">logout</a> first'
                                 ).format(provider=self.provider_session['provider']['bank']['name']))
        return True

    def process_message(self, message) -> Dictionarizable:
        """
        Parses the message looking for fixed strings or patterns, and calls the corresponding action
        @return
        the result of that action (it could be a message, a modal, ...)
        """
        normalized_message = normalize_string(message)

        # Check for exact provider names for login. Allow login only if user is not already logged in
        for provider in self.cache['providers']:
            if normalized_message == normalize_string(provider['name']):
                self.require_not_logged_in()
                return self.action_login(provider['code'])

        # Message processing cascade. All action methods must have a **kwargs parameter
        # that will be used to pass matching regex named groups, if any
        actions = (
            ActionSelector(_("_regex_logout"), self.action_logout, self.require_logged_in),
            ActionSelector(_("_regex_customer"), self.action_client, self.require_logged_in),
            ActionSelector(_("_regex_bank"), self.action_provider, self.require_not_logged_in),
            ActionSelector(_("_regex_account") + " +(?P<account_number>.*?) +" + _("_regex_movement")
                           + " *(?P<dates>.*)",
                           self.action_account_movement, self.require_logged_in),
            ActionSelector(_("_regex_account"), self.action_account, self.require_logged_in),
            ActionSelector(_("_regex_card") + " *(?P<card_number>.*?) *" + _("_regex_movement")
                           + " *(" + _("_regex_currency") + ")? *(?P<currency>[A-Za-z]{3}?)" + " *(?P<dates>.*)",
                           self.action_credit_card_movement, self.require_logged_in),
            ActionSelector(_("_regex_card"), self.action_card, self.require_logged_in),
            ActionSelector(_("_regex_info"), self.action_info, self.require_logged_in),
            ActionSelector(_("_regex_greeting"), lambda **kwargs: BotMessage(_("Hello! Nice to meet you :)")))
        )

        for action in actions:
            action_result = action.act_on(normalized_message)
            if action_result:
                return action_result

        return BotMessage(_("Sorry, could you give me more details about what you want to do?"))

    def action_provider(self, **kwargs) -> BotMessage:
        provider_response = meta.Provider(self.api_key).successful_json()

        banks_per_country = defaultdict(list)
        for bank in provider_response['providers']:
            banks_per_country[bank['country']].append(bank['name'])

        bank_string = _("The available banks per country are:") + "\n"
        for country, banks in sorted(banks_per_country.items()):
            bank_links = [f'<a class="message-link">{bank}</a>' for bank in banks]

            bank_string += country + ":\n" + "\n".join(bank_links) + "\n\n"

        return BotMessage(bank_string)

    def action_login(self, provider_code) -> ModalForm:
        provider_response = meta.ProviderDetail(self.api_key, provider_code=provider_code).successful_json()

        provider = provider_response['provider']
        self.provider_session = {'provider': provider}
        logo = provider['logo']

        provider_fields = [
            {'name': x['name'],
             'type': x['type'],
             'placeholder': x['label_es'] if self.request.LANGUAGE_CODE == 'es' else x['label_en']
             } for x in provider['auth_fields']
            if not x['interactive'] and not x['optional']
        ]

        self.provider_session['expected-fields'] = provider_fields

        return ModalForm('chatbot/provider_login.html',
                         ProviderLoginForm(provider_fields=provider_fields),
                         self.request,
                         logo=logo,
                         name=provider['bank']['name'])

    def action_logout(self, **kwargs) -> BotMessage:
        auth.Logout(self.api_key, self.provider_session.get('key')).successful_json()

        name = self.provider_session['provider']['bank']['name']
        del self.provider_session

        return BotMessage(_("Thank you for operating with ") + f"{name}")

    def action_client(self, **kwargs) -> BotMessage:
        client_response = auth.Client(self.api_key, self.provider_session.get('key')).successful_json()

        clients = client_response['clients']
        self.provider_session['clients'] = clients

        if len(clients) == 0:
            return BotMessage(_("There are no registered customers for this user"))

        client_names = [client for client in clients.values()]

        return BotMessage(client_names)

    def action_info(self, **kwargs):
        info_response = transactional.Info(self.api_key, self.provider_session.get('key')).successful_json()

        info = info_response['info']

        message = (_('Your info') + ":\n"
                   + _('ID') + f": {info['document']}\n"
                   + _('Name') + f": {info['name']}\n"
                   + _('email') + f": {info['email']}")

        return BotMessage(message)

    def action_account(self, **kwargs):
        # This is for translation purposes, so django can generate the .po with this strings
        translation_names = (_('balance') + _('branch') + _('currency')
                             + _('id') + _('name') + _('number'))

        message_parts = []
        for account in self.session_accounts:
            rows = [f'<div name="{key}" class="item row">'
                    '<div class="key">' + _(key) + ':</div>'
                                                   f'<div class="value">{value}</div>'
                                                   f'</div>' for key, value in account.items() if key != 'id']

            message_parts += [f'<div class="item link" name=\"{account["id"]}\">' + "\n".join(rows) + '</div>']

        return BotMessage("\n".join(message_parts))

    def action_account_movement(self, account_number=None, dates=None, **kwargs):
        if not account_number:
            return BotMessage(_('Please provide an account number...\n'
                                'Usage: "account <account number> movements"'))

        date_start, date_end = DateProcessor(language=self.request.LANGUAGE_CODE).get_valid_date_range(dates)

        movements = None
        for account in self.session_accounts:
            if account_number == account['number']:
                movements = transactional.AccountMovement(self.api_key,
                                                          self.provider_session.get('key'),
                                                          account_number=account_number,
                                                          currency=account['currency'],
                                                          date_start=date_start,
                                                          date_end=date_end
                                                          ).successful_json()

        if not movements:
            return BotMessage(_("Sorry, could not find that account..."
                                "Please check that the account number is correct..."))

        message_parts = []
        for movement in movements['movements']:
            rows = [f'<div name="{key}" class="item row">'
                    '<div class="key">' + _(key) + ':</div>'
                                                   f'<div class="value">{value}</div>'
                                                   f'</div>' for key, value in movement.items() if
                    key in ('reference', 'date', 'detail', 'debit', 'credit')]

            message_parts += [f'<div class="item link" name=\"{movement["id"]}\">' + "\n".join(rows) + '</div>']

        return BotMessage("\n".join(message_parts))

    def action_card(self, **kwargs):
        # This is for translation purposes, so django can generate the .po with this strings
        translation_names = (_('balance_dollar') + _('balance_local') + _('close_date')
                             + _('due_date') + _('id') + _('name') + _('number'))

        message_parts = []
        for card in self.session_credit_cards:
            rows = [f'<div name="{key}" class="item row">'
                    '<div class="key">' + _(key) + ':</div>'
                                                   f'<div class="value">{value}</div>'
                                                   f'</div>' for key, value in card.items() if key != 'id']

            message_parts += [f'<div class="item link" name=\"{card["id"]}\">' + "\n".join(rows) + '</div>']

        return BotMessage("\n".join(message_parts))

    def action_credit_card_movement(self, card_number=None, dates=None, currency: str = None, **kwargs):
        if not card_number:
            return BotMessage(_('Please provide a credit card number...\n'
                                'Usage: "card <card number> movements"'))

        if not currency or not re.match("[A-Z]{3}", currency.upper()):
            return BotMessage(_('Please provide a currency symbol for the transactions\n'
                                'e.g. USD for United States Dollars, UYU for Uruguayan peso'))

        date_start, date_end = DateProcessor(language=self.request.LANGUAGE_CODE).get_valid_date_range(dates)

        movements = None
        for credit_card in self.session_credit_cards:
            if card_number == credit_card['number']:
                movements = transactional.CreditCardMovement(self.api_key,
                                                             self.provider_session.get('key'),
                                                             card_number=card_number,
                                                             currency=currency.upper(),
                                                             date_start=date_start,
                                                             date_end=date_end
                                                             ).successful_json()

        if not movements:
            return BotMessage(_("Sorry, could not find that credit card..."
                                "Please check that the card number is correct..."))

        message_parts = []
        for movement in movements['movements']:
            rows = [f'<div name="{key}" class="item row">'
                    '<div class="key">' + _(key) + ':</div>'
                                                   f'<div class="value">{value}</div>'
                                                   f'</div>' for key, value in movement.items() if
                    key in ('reference', 'date', 'detail', 'debit', 'credit')]

            message_parts += [f'<div class="item link" name=\"{movement["id"]}\">' + "\n".join(rows) + '</div>']

        return BotMessage("\n".join(message_parts))


class ErrorResponse(JsonResponse):
    def __init__(self, content=None, **kwargs):
        kwargs.setdefault('status', 500)
        if content is None:
            content = _("Beep-bop! Something went wrong... Please try again later...")

        super().__init__(BotMessage(content).dict(), **kwargs)
