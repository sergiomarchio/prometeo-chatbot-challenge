from django.test import SimpleTestCase
from unittest.mock import patch

from parameterized import parameterized

from chatbot.api.api import ApiException
from chatbot.api.meta import Provider


@patch('requests.get')
class TestProvider(SimpleTestCase):
    api_key = "test_api_key"

    @parameterized.expand([
        (200, {"status": "success", "providers": None}),
        (200, {"status": "success", "providers": {}}),
    ])
    def test_successful_json_happy(self, mock_response, status_code, json):
        print()
        print("Testing behavior of successful_json() method - happy path scenario.")
        print("status code:", status_code)
        print("json:", json)

        mock_response.return_value.status_code = status_code
        mock_response.return_value.json.return_value = json

        self.assertEqual(Provider(self.api_key).successful_json(), json)

    @parameterized.expand([
        (200, None),
        (200, {}),
        (200, {"abc": "def"}),
        (200, {"status": "some-string"}),
        (200, {"status": "error"}),
        (200, {"status": "success"}),
        (200, {"status": "error", "providers": None}),
        (199, {"status": "success", "providers": None}),
        (300, {"status": "success", "providers": None}),
        (400, {"status": "success", "providers": None}),
        (500, {"status": "success", "providers": None}),
    ])
    def test_successful_json_failure(self, mock_response, status_code, json):
        print()
        print("Testing behavior of successful_json() method - failure scenario.")
        print("status code:", status_code)
        print("json:", json)

        mock_response.return_value.status_code = status_code
        mock_response.return_value.json.return_value = json

        self.assertRaises(ApiException, Provider(self.api_key).successful_json)
