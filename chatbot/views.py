from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .forms import LoginForm, ChatForm
from .models import API, MessageHistory


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
    if 'messages' not in request.session.keys():
        request.session['messages'] = MessageHistory()

    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            user_message = form.cleaned_data['text_field']

            request.session['messages'].add_user_message(user_message)
            print(request.session['messages'].messages)
            return HttpResponseRedirect(reverse('chatbot:chat'))
    else:
        form = ChatForm()

    # TODO delete this!
    print(request.session['api-key'])
    return render(request, 'chatbot/chat.html', {'form': form})
