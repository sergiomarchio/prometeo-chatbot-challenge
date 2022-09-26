import re
import unicodedata
from calendar import monthrange
from datetime import datetime
from typing import Optional, List, Tuple, Callable

from dateparser.date import DateDataParser
from dateparser.search import search_dates
from django.utils.translation import gettext as _


class Dictionarizable:
    def dict(self):
        """
        default implementation returns __dict__ object
        """
        return self.__dict__


class BotException(Exception):
    def __init__(self, message=''):
        super().__init__(message)
        self.message = message


class DateProcessor:
    """
    Class to model the processing of dates, including the search of dates inside strings
     and date range validations
    """
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

    def get_date_range(self, string=None) -> Optional[List[datetime]]:
        """
        Process a string looking for dates in any format.
        Parsing is done using dateparser package due to its flexibility.
        """
        if not string:
            return None

        dates = search_dates(string, languages=[self.language], settings=self.date_settings)

        if not dates:
            return None

        elif len(dates) == 2:
            # Get the string entered by the user to reprocess the dates and create range
            date_string_start, date_string_end = dates[0][0], dates[1][0]

            # Process the second date
            end_date = self.get_end_date(date_string_end)

            # Get the first date relative to the second date,
            # in order to get consistent results if range is something like "december to january"
            start_date = self.get_start_date(date_string_start, end_date)

            return [start_date, end_date]

        elif len(dates) == 1:
            # Date entered by the user
            date_string = dates[0][0]
            return [self.get_start_date(date_string), self.get_end_date(date_string)]

        return None

    def get_valid_date_range(self, string: str) -> Tuple[datetime, datetime]:
        """
        @return
        a valid date range in the past (start date < end date < now)
        raises Exception if range is not valid
        """
        date_range = self.get_date_range(string)

        if not date_range:
            raise BotException(_("Sorry, could not get the dates... \n"
                                 "please check that you are using a valid format\n"
                                 "You can use words like 'july'\n"
                                 "or the date format dd/mm/YYYY, e.g. 31/12/1999"))

        date_start, date_end = date_range
        if date_start > date_end:
            raise BotException(_("Sorry, the first date must be before the second date..."))

        if date_end > datetime.today():
            raise BotException(_("Sorry, I can't see the future... yet ;)"))

        return date_start, date_end


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
        print("criteria", self.selection_criteria, "-------------")
        if match and (not self.precondition or self.precondition()):
            return self.action(**match.groupdict())

        return None


def normalize_string(string):
    return (unicodedata.normalize('NFD', string)
            .encode('ascii', 'ignore').decode()
            .lower())
