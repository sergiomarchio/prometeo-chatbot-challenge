from datetime import datetime

from .api import Api, Method


class Info(Api):
    parameters = "info/"
    method = Method.GET

    def __init__(self, api_key, key):
        super().__init__(api_key, query_params={'key': key})

    def is_ok(self) -> bool:
        return (self.response.status_code == 200
                and self.response_json.get('status') == "success"
                and 'info' in self.response_json)


class Account(Api):
    parameters = "account/"
    method = Method.GET

    def __init__(self, api_key, key):
        super().__init__(api_key, query_params={'key': key})

    def is_ok(self) -> bool:
        return (self.response.status_code == 200
                and self.response_json.get('status') == "success"
                and 'accounts' in self.response_json)


class AccountMovement(Api):
    parameters = "account/{account_number}/movement/"
    method = Method.GET
    date_format = "%d/%m/%Y"

    def __init__(self, api_key, key, account_number, currency, date_start: datetime, date_end: datetime):
        super().__init__(api_key,
                         path_params={'account_number': account_number},
                         query_params={'key': key,
                                       'currency': currency,
                                       'date_start': date_start.strftime(self.date_format),
                                       'date_end': date_end.strftime(self.date_format)
                                       })

    def is_ok(self) -> bool:
        return (self.response.status_code == 200
                and self.response_json.get('status') == "success"
                and 'movements' in self.response_json)


class CreditCard(Api):
    parameters = "credit-card/"
    method = Method.GET

    def __init__(self, api_key, key):
        super().__init__(api_key, query_params={'key': key})

    def is_ok(self) -> bool:
        return (self.response.status_code == 200
                and self.response_json.get('status') == "success"
                and 'credit_cards' in self.response_json)
