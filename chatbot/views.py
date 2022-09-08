from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


def homepage(request):
    return render(request, 'chatbot/login.html')
