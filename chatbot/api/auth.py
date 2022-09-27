from .api import Api, Method


class Login(Api):
    parameters = "login/"
    method = Method.POST

    def __init__(self, api_key, key=None, data=None):
        super().__init__(api_key, query_params={'key': key}, data=data)
        self.headers["accept"] = "application/json"
        self.headers["content-type"] = "application/x-www-form-urlencoded"

    def is_ok(self):
        """
        contract from https://docs.prometeoapi.com/reference/login
        """
        return (self.response.status_code == 200
                and 'key' in self.response_json
                and 'status' in self.response_json)


class Logout(Api):
    parameters = "logout/"
    method = Method.GET

    def __init__(self, api_key, key):
        super().__init__(api_key, query_params={'key': key})

    def is_ok(self) -> bool:
        """
        contract from https://docs.prometeoapi.com/reference/logout
        """
        return (self.response.status_code == 200
                and self.response_json.get('status') == "logged_out")


class Client(Api):
    parameters = "client/"
    method = Method.GET

    def __init__(self, api_key, key):
        super().__init__(api_key, query_params={'key': key})

    def is_ok(self) -> bool:
        """
        contract from https://docs.prometeoapi.com/reference/getclients
        """
        return (self.response.status_code == 200
                and self.response_json.get('status') == "success"
                and "clients" in self.response_json)


class ClientSelect(Api):
    parameters = "client/{client_id}/"
    method = Method.GET

    def __init__(self, api_key, key, client_id):
        super().__init__(api_key, path_params={'client_id': client_id}, query_params={'key': key})

    def is_ok(self) -> bool:
        """
        contract from https://docs.prometeoapi.com/reference/selectclient
        """
        return (self.response.status_code == 200
                and self.response_json.get('status') == "success")
