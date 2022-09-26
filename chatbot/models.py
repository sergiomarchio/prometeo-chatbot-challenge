from collections import defaultdict
from calendar import monthrange
from datetime import datetime

from dateparser.date import DateDataParser
from dateparser.search import search_dates
from django import forms
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
import re
from typing import List, Optional, Callable
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


class DateProcessor:

    def __init__(self, language='en'):
        self.language = language
        self.date_settings = {'DATE_ORDER': 'DMY' if language == 'es' else 'MDY',
                              'PREFER_DATES_FROM': 'past'}
        self.date_parser = DateDataParser(languages=[self.language], settings=self.date_settings)

    def get_start_date(self, string: str, relative_to: datetime = None) -> datetime:
        """
        Returns the starting date of the provided date period string
        """
        if relative_to:
            date_parser = DateDataParser(languages=[self.language],
                                         settings={**self.date_settings, **{'RELATIVE_BASE': relative_to}})
        else:
            date_parser = self.date_parser

        date_data = date_parser.get_date_data(string)
        start_date = date_data.date_obj

        # Get the first day of the corresponding period, if it's not "day"
        if date_data.period == 'year':
            start_date = start_date.replace(month=1, day=1)
        elif date_data.period == 'month':
            start_date = start_date.replace(day=1)

        return start_date

    def get_end_date(self, string: str) -> datetime:
        """
        Returns the ending date of the provided date period string
        """
        date_data = self.date_parser.get_date_data(string)
        start_date = date_data.date_obj

        # Get the last day of the corresponding period, if it's not "day"
        if date_data.period == 'year':
            start_date = start_date.replace(month=12, day=31)
        elif date_data.period == 'month':
            last_day_in_month = monthrange(year=start_date.year, month=start_date.month)[1]
            start_date = start_date.replace(day=last_day_in_month)

        return start_date

    def get_date_range(self, string) -> Optional[List[datetime]]:
        """
        Process a string looking for dates in any format.
        Parsing is done using dateparser package due to its flexibility.
        """
        dates = search_dates(string, languages=[self.language], settings=self.date_settings)

        if not dates:
            return None

        elif len(dates) == 2:
            # Get the string entered by the user to reprocess the dates and create range
            date_string_start, date_string_end = dates[0][0], dates[1][0]

            # Process the second date
            end_date = self.get_end_date(string)

            # Get the first date relative to the second date,
            # in order to get consistent results if range is something like "december to january"
            start_date = self.get_start_date(string, end_date)

            return [start_date, end_date]

        elif len(dates) == 1:
            # Date entered by the user
            date_string = dates[0][0]
            return [self.get_start_date(date_string), self.get_end_date(date_string)]

        return None


class BotException(Exception):
    def __init__(self, message=''):
        super().__init__(message)
        self.message = message


class ActionSelector:
    """
    Defines the object used to select an action, based on a string (message)
    by applying a regex criteria if the precondition is met
    """

    def __init__(self, selection_criteria: str, action: Callable, precondition: Callable[[], bool] = None):
        self.selection_criteria = selection_criteria
        self.action = action
        self.precondition = precondition

    def act_on(self, string):
        """
        Checks if the criteria regex has any match in the target string.
        If so, calls the action passing as parameters the named groups that matches,
        returning the result of the action if the precondition is met
        """
        match = re.search(self.selection_criteria, string)
        if match and (not self.precondition or self.precondition()):
            print("I'm in!")
            return self.action(**match.groupdict())

        return None


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
                                 ).format(provider=self.provider_session['name']))
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
            ActionSelector(_("log *out"), self.action_logout, self.require_logged_in),
            ActionSelector(_("customers?"), self.action_client, self.require_logged_in),
            ActionSelector(_("banks?"), self.action_provider, self.require_not_logged_in),
            ActionSelector(_("_regex_account") + " +(?P<account_number>.*?) +" + _("_regex_movement")
                           + " *(?P<dates>.*?)",
                           self.action_account_movement, self.require_logged_in),
            ActionSelector(_("accounts?"), self.action_account, self.require_logged_in),
            ActionSelector(_("cards?"), self.action_card, self.require_logged_in),
            ActionSelector(_("(data)|(info)"), self.action_info, self.require_logged_in),
            ActionSelector(_("(hi)|(hello)"), lambda **kwargs: BotMessage(_("Hello! Nice to meet you :)")))
        )

        for action in actions:
            action_result = action.act_on(normalized_message)
            if action_result:
                return action_result

        return BotMessage(_("Sorry, could you give me more details about what you want to do?"))

    def action_provider(self, **kwargs) -> BotMessage:
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

        return ModalForm('chatbot/provider_login.html',
                         ProviderLoginForm(provider_fields=provider_fields),
                         self.request,
                         logo=logo,
                         name=provider['bank']['name'])

    def action_logout(self, **kwargs) -> BotMessage:
        auth.Logout(self.api_key, self.provider_session.get('key')).validate_response()

        name = self.provider_session['bank']['name']
        del self.provider_session

        return BotMessage(_("Thank you for operating with ") + f"{name}")

    def action_client(self, **kwargs) -> BotMessage:
        client_api = auth.Client(self.api_key, self.provider_session.get('key'))
        client_api.validate_response()
        client_response = client_api.response_json

        clients = client_response['clients']
        self.provider_session['clients'] = clients

        if len(clients) == 0:
            return BotMessage(_("There are no registered customers for this user"))

        client_names = [client for client in clients.values()]

        return BotMessage(client_names)

    def action_info(self, **kwargs):
        info_api = transactional.Info(self.api_key, self.provider_session.get('key'))
        info_api.validate_response()
        info_response = info_api.response_json

        info = info_response['info']

        message = (_('Your info') + ":\n"
                   + _('ID') + f": {info['document']}\n"
                   + _('Name') + f": {info['name']}\n"
                   + _('email') + f": {info['email']}")

        return BotMessage(message)

    def action_account(self, **kwargs):
        account_api = transactional.Account(self.api_key, self.provider_session.get('key'))
        account_api.validate_response()
        account_response = account_api.response_json

        accounts = account_response['accounts']
        self.provider_session['accounts'] = accounts

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

    def action_account_movement(self, account_number=None, dates=None, **kwargs):
        if not account_number:
            return BotMessage(_('Please provide an account number...\n'
                                'Usage: "account <account number> movements"'))

        if 'accounts' not in self.provider_session:
            self.provider_session['accounts'] = transactional.Account(self.api_key,
                                                                      self.provider_session.get('key')).response_json

        if not dates:
            return BotMessage(_("Please enter the dates that you want to check for account movements\n"))

        date_range = DateProcessor(language=self.request.LANGUAGE_CODE).get_date_range(dates)
        if not date_range:
            return BotMessage(_("Sorry, could not get the dates, try using words like 'august 2020' "
                                "or with the format dd/mm/YYYY"))

        date_start, date_end = date_range
        if date_start > date_end:
            return BotMessage(_("Sorry, the first date must be before the second date..."))

        movements = None

        for account in self.provider_session['accounts']['accounts']:
            if account_number == account['number']:
                movements = transactional.AccountMovement(self.api_key,
                                                          self.provider_session.get('key'),
                                                          account_number=account_number,
                                                          currency=account['currency'],
                                                          date_start=date_start,
                                                          date_end=date_end
                                                          ).response_json

        if not movements:
            return BotMessage(_("Sorry, could not find that account..."
                                "Please check that the account number is correct..."))

        message_parts = []
        for movement in movements['movements']:
            rows = [f'<div name="{key}" class="item row">'
                    '<div class="key">' + _(key) + ':</div>'
                                                   f'<div class="value">{value}</div>'
                                                   f'</div>' for key, value in movement.items() if
                    key in ('date', 'detail', 'debit', 'credit')]

            message_parts += [f'<div class="item link" name=\"{movement["id"]}\">' + "\n".join(rows) + '</div>']

        return BotMessage("\n".join(message_parts))

    def action_card(self, **kwargs):
        card_api = transactional.Card(self.api_key, self.provider_session.get('key'))
        card_api.validate_response()
        card_response = card_api.response_json

        cards = card_response['credit_cards']
        self.provider_session['cards'] = cards

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
