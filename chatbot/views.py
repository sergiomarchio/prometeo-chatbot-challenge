from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse

import json

from .forms import LoginForm, ChatForm
from .models import ApiKey, BotMessage, UserMessage, MessageHistory, MessageProcessor


def homepage(request):

    if 'message_history' in request.session.keys():
        return HttpResponseRedirect(reverse('chatbot:chat'))

    return render(request, 'chatbot/index.html')


def guest(request):
    request.session['api-key'] = ApiKey.guest_key()

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


def process_message(request):
    """
    Processes the message from the user (sent via AJAX) and returns the bot response.
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not is_ajax:
        return HttpResponseBadRequest()

    if not request.method == 'POST':
        return JsonResponse({'status': 'Invalid request'}, status=400)

    user_message = json.loads(request.body)
    print(user_message)

    if user_message.get('sender') != 'user':
        return JsonResponse({'status': 'Invalid request'}, status=400)

    user_message_content = user_message.get('content')
    print(request.session['api-key'])

    request.session['message_history'].add(UserMessage(user_message_content))

    bot_message_content = MessageProcessor(request.session['api-key']).process_message(user_message_content)
    bot_message = BotMessage(bot_message_content)

    request.session['message_history'].add(bot_message)

    print(request.session['message_history'])

    return JsonResponse(bot_message.__dict__, status=200)


def chat(request):
    if 'message_history' not in request.session.keys():
        request.session['message_history'] = MessageHistory()

    form = ChatForm()

    context = {
        'form': form,
        'message_history': request.session['message_history']
    }

    return render(request, 'chatbot/chat.html', context)
