from .api import Api, Method


class Login(Api):
    parameters = "login/"
    method = Method.POST

    def __init__(self, api_key, key=None, data=None):
        super().__init__(api_key, query_params={'key': key} if key is not None else None, data=data)
        self.headers["accept"] = "application/json"
        self.headers["content-type"] = "application/x-www-form-urlencoded"

    def is_ok(self):
        return (self.response.status_code == 200
                and 'key' in self.response_json
                and 'status' in self.response_json)


class Logout(Api):
    parameters = "logout/"
    method = Method.GET

    def __init__(self, api_key, key):
        super().__init__(api_key, query_params={'key': key})

    def is_ok(self) -> bool:
        return self.response_json.get('status') == "logged_out"
