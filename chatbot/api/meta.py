from .api import Api, Method


class Provider(Api):
    parameters = "provider/"
    method = Method.GET

    def is_ok(self):
        """
        contract from https://docs.prometeoapi.com/reference/getproviders
        """
        return (self.response.status_code == 200
                and self.response_json.get('status') == "success"
                and "providers" in self.response_json)


class ProviderDetail(Api):
    parameters = "provider/{provider_code}/"
    method = Method.GET

    def __init__(self, api_key, provider_code):
        super().__init__(api_key, path_params={'provider_code': provider_code})

    def is_ok(self) -> bool:
        """
        contract from https://docs.prometeoapi.com/reference/getproviderdetail
        """
        return (self.response.status_code == 200
                and self.response_json.get('status') == "success"
                and "provider" in self.response_json)


class ProviderBranches(Api):
    parameters = "provider/{provider_code}/branches"
    method = Method.GET

    def __init__(self, api_key, provider_code, zip_code):
        super().__init__(api_key, path_params={'code': provider_code}, query_params={'zip': zip_code})

    def is_ok(self) -> bool:
        """
        contract from https://docs.prometeoapi.com/reference/getproviderbranches
        """
        return (self.response.status_code == 200
                and self.response_json.get('status') == "success"
                and "branches" in self.response_json)


class ProviderAtm(Api):
    parameters = "provider/{provider_code}/atms"
    method = Method.GET

    def __init__(self, api_key, provider_code, zip_code):
        super().__init__(api_key, path_params={'code': provider_code}, query_params={'zip': zip_code})

    def is_ok(self) -> bool:
        """
        contract from https://docs.prometeoapi.com/reference/getprovideratms
        """
        return (self.response.status_code == 200
                and self.response_json.get('status') == "success"
                and "branches" in self.response_json)
