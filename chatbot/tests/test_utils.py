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
        print()
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


class TestActionSelector(SimpleTestCase):

    def action_true(self):
        return True

    def action_groups(self, **kwargs):
        return kwargs

    def raise_bot_exception(self):
        raise utils.BotException()

    @parameterized.expand([
        ("hi this is a test", "."),
        ("hi this is a test", "this"),
        ("hi this is a test", "is ?a"),
    ])
    def test_act_on_happy(self, string, criteria):
        print()
        print("Testing behavior of ActionSelector.act_on method - happy path scenario.")
        print("string:", string)
        print("criteria:", criteria)

        self.assertTrue(utils.ActionSelector(criteria, self.action_true).act_on(string))

    @parameterized.expand([
        ("hi this is a test", "abcdef"),
    ])
    def test_act_on_failure(self, string, criteria):
        print()
        print("Testing behavior of ActionSelector.act_on method - failure scenario.")
        print("string:", string)
        print("criteria:", criteria)

        self.assertIsNone(utils.ActionSelector(criteria, self.action_true).act_on(string))

    @parameterized.expand([
        ("hi this is a test", ".", {}),
        ("hi this is a test", "this", {}),
        ("hi this is a test", "abcdef", None),
        ("hi this is a test", "(?P<group1>test)", {"group1": "test"}),
        ("hi this is a test", "(?P<g1>this).*?(?P<g2>test)", {"g1": "this", "g2": "test"}),
    ])
    def test_act_on_groups(self, string, criteria, expected_groups):
        print()
        print("Testing behavior of ActionSelector.act_on method - with groups.")
        print("string:", string)
        print("criteria:", criteria)
        print("expected_groups:", expected_groups)

        self.assertEqual(utils.ActionSelector(criteria, self.action_groups).act_on(string), expected_groups)

    @parameterized.expand([
        ("hi this is a test", ".", {}),
        ("hi this is a test", "this", {}),
        ("hi this is a test", "abcdef", None),
        ("hi this is a test", "(?P<group1>test)", {"group1": "test"}),
        ("hi this is a test", "(?P<g1>this).*?(?P<g2>test)", {"g1": "this", "g2": "test"}),
    ])
    def test_act_on_precondition(self, string, criteria, expected_groups):
        print()
        print("Testing behavior of ActionSelector.act_on method - with precondition.")
        print("string:", string)
        print("criteria:", criteria)
        print("expected_groups:", expected_groups)

        self.assertEqual(utils.ActionSelector(criteria, self.action_groups, lambda: True).act_on(string),
                         expected_groups)

    @parameterized.expand([
        ("hi this is a test", "."),
        ("hi this is a test", "this"),
        ("hi this is a test", "abcdef"),
        ("hi this is a test", "(?P<group1>test)"),
        ("hi this is a test", "(?P<g1>this).*?(?P<g2>test)"),
    ])
    def test_act_on_precondition_fail(self, string, criteria):
        print()
        print("Testing behavior of ActionSelector.act_on method - with precondition not met.")
        print("string:", string)
        print("criteria:", criteria)

        self.assertIsNone(utils.ActionSelector(criteria, self.action_groups, lambda: False).act_on(string))

    @parameterized.expand([
        ("hi this is a test", "."),
        ("hi this is a test", "this"),
        ("hi this is a test", "(?P<group1>test)"),
        ("hi this is a test", "(?P<g1>this).*?(?P<g2>test)"),
    ])
    def test_act_on_precondition_exception(self, string, criteria):
        print()
        print("Testing behavior of ActionSelector.act_on method - with precondition raising exception.")
        print("string:", string)
        print("criteria:", criteria)

        self.assertRaises(utils.BotException, utils.ActionSelector(criteria, self.action_groups,
                                                                   self.raise_bot_exception
                                                                   ).act_on, string)
