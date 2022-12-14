import functools
import traceback

from django.core.exceptions import BadRequest
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from .api import api, auth, meta
from .forms import LoginForm, ChatForm, ProviderLoginForm
from .models import ApiKey, MessageHistory, MessageProcessor, \
    Message, BotMessage, UserMessage, \
    ErrorResponse, ModalForm
from .utils import BotException


def log_me_in(session: dict, api_key: str) -> bool:
    """
    Validates the key by requesting the provider list
    saves the api key in the session
    creates an empty dict to store cached responses
    """

    # Get bank list to validate API key
    provider_api = meta.Provider(api_key)

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


def close(request):
    """
    Closes the chat, clearing the session and returning to home page
    """
    request.session.flush()

    return HttpResponseRedirect(reverse('chatbot:homepage'))


def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def require_ajax(view):
    """
    Decorator to allow only AJAX requests in the decorated view
    """
    @functools.wraps(view)
    def wrapper(request):
        if not is_ajax(request):
            print("request is not AJAX...")
            raise BadRequest

        return view(request)

    return wrapper


@require_ajax
@require_POST
def process_message(request):
    """
    Processes the message from the user (sent via AJAX) and returns the bot response.
    """
    if ('cache' not in request.session
            or 'message_history' not in request.session
            or 'api-key' not in request.session['cache']):

        return ErrorResponse()

    chat_form = ChatForm(request.POST)

    if not chat_form.is_valid():
        print("Invalid form... ChatForm")
        return ErrorResponse()

    user_message_content = chat_form.cleaned_data['text_field']
    user_message = UserMessage(user_message_content)

    request.session['message_history'].add(user_message)

    try:
        processing_result = MessageProcessor(request.session['cache'], request).process_message(user_message_content)
    except BotException as e:
        processing_result = BotMessage(e.message)
    except api.ApiException as e:
        return ErrorResponse(f"Beep-bop! {e.message}", status=e.status)
    except Exception as e:
        print("Exception: ", e)
        print(traceback.format_exc())

        return ErrorResponse()

    if isinstance(processing_result, Message):
        request.session['message_history'].add(processing_result)

    print()
    print(request.session['cache']['api-key'])
    print("language", request.LANGUAGE_CODE)
    print(processing_result)

    return JsonResponse(processing_result.dict(), status=200)


@require_ajax
@require_POST
def provider_login(request):
    """
    Processes the login request for a provider (sent via AJAX).
    """
    provider_session = request.session['cache']['provider_session']
    expected_fields = provider_session['expected-fields']

    provider_login_form = ProviderLoginForm(request.POST, provider_fields=expected_fields)
    if not provider_login_form.is_valid():
        print("Invalid form... ProviderLoginForm")
        return ErrorResponse()

    provider = provider_session['provider']
    credentials = {
        "provider": provider['name'],
        **provider_login_form.cleaned_data,
        **provider_session.get("credentials", {})
    }

    login = auth.Login(request.session['cache']['api-key'],
                       key=provider_session.get('key'), data=credentials)

    status = login.response_json.get('status')

    if status == "error":
        message = login.response_json['message']
        if message == "Unauthorized provider":
            return ErrorResponse(_('Sorry, this provider is not available at the moment...'),
                                 status=400)

    elif status == "wrong_credentials":
        return JsonResponse({'modal-feedback': _('Wrong credentials!')}, status=400)

    login_response = login.successful_json()

    provider_session['key'] = login_response['key']

    if status == "logged_in":
        del provider_session['expected-fields']

        message = BotMessage(_('Successfully logged in!\n'
                               'To log out from this provider type <a class="message-link">logout</a>.\n'
                               'You can try also:\n'
                               '<a class="message-link">info</a> for your personal information\n'
                               '<a class="message-link">accounts</a> for your accounts in this provider\n'
                               '<a class="message-link">cards</a> for your cards in this provider'
                               ))

        request.session['message_history'].add(message)

        return JsonResponse(message.dict(), status=200)

    elif status == "interaction_required":
        provider_session['credentials'] = credentials
        logo = provider['logo']

        provider_fields = [
            {'name': x['name'],
             'type': x['type'],
             'label': login_response['context'],
             'placeholder': x['label_es'] if request.LANGUAGE_CODE == 'es' else x['label_en']
             } for x in provider['auth_fields']
            if x['interactive'] and x['name'] == login_response['field']
        ]

        provider_session['expected-fields'] = provider_fields

        return JsonResponse(ModalForm('chatbot/provider_login.html',
                                      ProviderLoginForm(provider_fields=provider_fields),
                                      request,
                                      logo=logo,
                                      name=provider['bank']['name']).dict(),
                            status=200)

    return ErrorResponse()


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
        messages.add(BotMessage(_('Hi! What do you want to do in Prometeo today?\n'
                                  'You can start by typing <a class="message-link">banks</a>.\n'
                                  'If my messages have links, you can click them and I will write that for you :)')))
        request.session['message_history'] = messages

    form = ChatForm()

    context = {
        'form': form,
        'message_history': request.session['message_history']
    }

    return render(request, 'chatbot/chat.html', context)
