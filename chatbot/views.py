from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import json

from .forms import LoginForm, ChatForm
from .models import ApiKey, BotMessage, UserMessage, MessageHistory, MessageProcessor


def homepage(request):
    """
    Homepage if no user is logged in.
    If a user is logged in, redirects to chat page.
    """
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
    """
    Logs out and returns to home page
    """
    request.session.flush()

    return HttpResponseRedirect(reverse('chatbot:homepage'))


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

    try:
        bot_message_content = MessageProcessor(request.session['api-key']).process_message(user_message_content)
    except ValueError as e:
        return JsonResponse(BotMessage(str(e)).__dict__, status=500)
    except Exception as e:
        message = _("There was an unexpected error... Please try again later")
        return JsonResponse(BotMessage(message).__dict__, status=500)

    bot_message = BotMessage(bot_message_content)

    request.session['message_history'].add(bot_message)

    print(request.session['message_history'])

    return JsonResponse(bot_message.__dict__, status=200)


def chat(request):
    """
    Main view for chat window.
    The first time it's loaded, it creates a welcome message
    """
    if 'message_history' not in request.session.keys():
        messages = MessageHistory()
        messages.add(BotMessage(_("Hi! What do you want to do with Prometeo today?")))
        request.session['message_history'] = messages

    form = ChatForm()

    context = {
        'form': form,
        'message_history': request.session['message_history']
    }

    return render(request, 'chatbot/chat.html', context)
