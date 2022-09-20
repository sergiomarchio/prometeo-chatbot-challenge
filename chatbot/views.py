from django.core.exceptions import BadRequest
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import json

from . import api
from .forms import LoginForm, ChatForm
from .models import ApiKey, Message, BotMessage, UserMessage, MessageHistory, MessageProcessor


def log_me_in(session: dict, api_key: str) -> bool:
    """
    Validates the  key by requesting the provider list
    saves the api key in the session
    creates an empty dict to store cached responses
    """

    # Get bank list to validate API key
    provider_api = api.Provider(api_key)

    if provider_api.is_ok():
        session['cache'] = {}
        session['cache']['api-key'] = api_key
        session['cache']['providers'] = provider_api.response_json['providers']

        return True

    return False


def homepage(request):
    """
    Homepage if no user is logged in.
    If a user is logged in, redirects to chat page.
    """
    if 'message_history' in request.session:
        return HttpResponseRedirect(reverse('chatbot:chat'))

    if request.method == 'POST':
        login_form = LoginForm(request.POST)

        if login_form.is_valid() and log_me_in(request.session, login_form.cleaned_data['api_key']):
            return HttpResponseRedirect(reverse('chatbot:chat'))

    return render(request, 'chatbot/index.html', {'login_form': LoginForm()})


def guest(request):
    if log_me_in(request.session, ApiKey.guest_key()):
        return HttpResponseRedirect(reverse('chatbot:chat'))


def logout(request):
    """
    Logs out and returns to home page
    """
    request.session.flush()

    return HttpResponseRedirect(reverse('chatbot:homepage'))


def validate_ajax(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not is_ajax or request.method != 'POST':
        raise BadRequest


def process_message(request):
    """
    Processes the message from the user (sent via AJAX) and returns the bot response.
    """
    validate_ajax(request)

    if ('cache' not in request.session
            or 'message_history' not in request.session
            or 'api-key' not in request.session['cache']):

        message = _("There was an unexpected error... Please log in again")
        return JsonResponse(BotMessage(message).dict(), status=400)

    user_message = json.loads(request.body)
    print(user_message)

    if user_message.get('sender') != 'user':
        return JsonResponse({'status': 'Invalid request'}, status=400)

    user_message_content = user_message.get('content')
    request.session['message_history'].add(UserMessage(user_message_content))

    try:
        bot_response = MessageProcessor(request.session['cache'], request).process_message(user_message_content)
    except Exception as e:
        print("Exception: ", e)
        print(e.with_traceback())
        message = _("There was an unexpected error... Please try again later")
        return JsonResponse(BotMessage(message).dict(), status=500)

    if isinstance(bot_response, Message):
        request.session['message_history'].add(bot_response)
        # print(request.session['message_history'])

    print()
    print(request.session['cache']['api-key'])
    print("language", request.LANGUAGE_CODE)
    print(bot_response)

    return JsonResponse(bot_response.dict(), status=200)


def provider_login(request):
    """
    Processes the login request for a provider (sent via AJAX).
    """
    validate_ajax(request)

    credentials = json.loads(request.body)

    # TODO remove
    print(credentials)

    credentials["provider"] = request.session['cache']['active_provider']['provider']['name']
    # TODO remove
    print(credentials)

    login = api.Login(request.session['cache']['api-key'], **credentials)

    if login.is_ok():
        request.session['cache']['active_provider']['key'] = login.response_json['key']
        return JsonResponse(BotMessage(_('Successfully logged in!')).dict(), status=200)

    status = login.response_json['status']
    if status == "wrong_credentials":
        return JsonResponse(BotMessage(_('Wrong credentials!')).dict(), status=400)
    elif status == "error":
        message = login.response_json['message']
        if message == "Unauthorized provider":
            return JsonResponse(BotMessage(_('Sorry, this provider is not available at the moment...')).dict(),
                                status=400)

    return JsonResponse(BotMessage('Logging into...').dict(), status=200)


def chat(request):
    """
    Main view for chat window.
    The first time it's loaded, it creates a welcome message
    """
    # If there is no API key (the user entered the url directly) redirect to home page
    if ('cache' not in request.session
            or 'api-key' not in request.session['cache']):

        return HttpResponseRedirect(reverse('chatbot:homepage'))

    if 'message_history' not in request.session:
        messages = MessageHistory()
        messages.add(BotMessage(_("Hi! What do you want to do in Prometeo today?")))
        request.session['message_history'] = messages

    form = ChatForm()

    context = {
        'form': form,
        'message_history': request.session['message_history']
    }

    return render(request, 'chatbot/chat.html', context)
