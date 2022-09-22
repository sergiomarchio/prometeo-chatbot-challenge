from .api import Api, Method


class Provider(Api):
    parameters = "provider/"
    method = Method.GET

    def is_ok(self):
        return (200 <= self.response.status_code < 300
                and self.response_json.get('status') == "success"
                and "providers" in self.response_json)


class ProviderDetail(Api):
    parameters = "provider/{provider_code}/"
    method = Method.GET

    def __init__(self, api_key, provider_code):
        super().__init__(api_key, path_params={'provider_code': provider_code})

    def is_ok(self) -> bool:
        return (200 <= self.response.status_code < 300
                and self.response_json.get('status') == "success")


class ProviderBranches(Api):
    parameters = "provider/{provider_code}/branches"
    method = Method.GET

    def __init__(self, api_key, provider_code, zip_code):
        super().__init__(api_key, path_params={'code': provider_code}, query_params={'zip': zip_code})

    def is_ok(self) -> bool:
        return (200 <= self.response.status_code < 300
                and self.response_json.get('status') == "success")


class ProviderAtm(Api):
    parameters = "provider/{provider_code}/atms"
    method = Method.GET

    def __init__(self, api_key, provider_code, zip_code):
        super().__init__(api_key, path_params={'code': provider_code}, query_params={'zip': zip_code})

    def is_ok(self) -> bool:
        return (200 <= self.response.status_code < 300
                and self.response_json.get('status') == "success")
