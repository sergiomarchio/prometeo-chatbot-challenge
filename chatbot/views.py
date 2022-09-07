from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _


def homepage(request):
    return HttpResponse(_("Hello!"))
