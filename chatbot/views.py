from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .forms import LoginForm, ChatForm
from .models import API, BotMessage, UserMessage, MessageHistory


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


def logout(request):
    request.session.flush()
    return HttpResponse()


def chat(request):
    if 'message_history' not in request.session.keys():
        request.session['message_history'] = MessageHistory()

    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            user_message = form.cleaned_data['text_field']

            request.session['message_history'].add(UserMessage(user_message))
            request.session['message_history'].add(BotMessage("ok"))

            print(request.session['message_history'])

            return HttpResponseRedirect(reverse('chatbot:chat'))
    else:
        form = ChatForm()

    # TODO delete this!
    print(request.session['api-key'])
    context = {
        'form': form,
        'message_history': request.session['message_history']
    }

    return render(request, 'chatbot/chat.html', context)
