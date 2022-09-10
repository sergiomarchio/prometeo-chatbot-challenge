from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .forms import LoginForm
from .models import API


def homepage(request):
    return render(request, 'chatbot/index.html')


def guest(request):
    request.session['api-key'] = API.guest_key()

    return render(request, 'chatbot/guest.html')


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            request.session['api-key'] = form.cleaned_data['api_key']

            return HttpResponseRedirect(reverse('chatbot:chat'))
    else:
        form = LoginForm()

    return render(request, 'chatbot/login.html', {'form': form})


def chat(request):

    print(request.session['api-key'])
    return render(request, 'chatbot/chat.html')
