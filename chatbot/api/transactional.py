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


class Card(Api):
    parameters = "credit-card/"
    method = Method.GET

    def __init__(self, api_key, key):
        super().__init__(api_key, query_params={'key': key})

    def is_ok(self) -> bool:
        return (self.response.status_code == 200
                and self.response_json.get('status') == "success"
                and 'credit_cards' in self.response_json)
