from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from .models import BotMessage


class Dictionarizable:
    def dict(self):
        """
        default implementation returns __dict__ object
        """
        return self.__dict__


def bot_response(message, status):
    return JsonResponse(BotMessage(message).dict(), status=status)


def default_error_response(status=500):
    return JsonResponse(BotMessage(_("Something went wrong... Please try again later...")).dict(), status=status)

