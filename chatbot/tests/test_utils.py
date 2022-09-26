from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.test import SimpleTestCase
from parameterized import parameterized

import chatbot.utils as utils


class TestDateProcessor(SimpleTestCase):
    language = 'en'
    date_format = "%d/%m/%Y"
    future_date = (datetime.today() + relativedelta(years=1)).strftime(date_format)
    present_date = datetime.today().strftime(date_format)
    past_date = (datetime.today() - relativedelta(years=1)).strftime(date_format)

    def setUp(self) -> None:
        self.date_processor = utils.DateProcessor(language=self.language)
        print(f"Setting DateProcessor language to '{self.language}'")

    @parameterized.expand([
        future_date,
        f"{past_date} {future_date}",
        f"{future_date} {past_date}",
        f"{future_date} {future_date}",
        f"{present_date} {future_date}",
        f"{future_date} {present_date}",
    ])
    def test_future_date(self, date_string):
        print(f"Validating that future date raises exception, with date string '{date_string}'")
        self.assertRaises(utils.BotException, self.date_processor.get_valid_date_range, date_string)

    @parameterized.expand([
        f"{present_date} {past_date}",
    ])
    def test_incorrect_date_order(self, date_string):
        print(f"Validating that incorrect date order raises exception, with date string '{date_string}'")
        self.assertRaises(utils.BotException, self.date_processor.get_valid_date_range, date_string)


class TestDateProcessorEs(TestDateProcessor):
    language = 'es'
