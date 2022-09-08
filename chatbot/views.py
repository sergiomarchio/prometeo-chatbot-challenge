from django.shortcuts import render


def homepage(request):
    return render(request, 'chatbot/index.html')


def guest(request):
    return render(request, 'chatbot/guest.html')


def login(request):
    return render(request, 'chatbot/login.html')
