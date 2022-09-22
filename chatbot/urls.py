from django.urls import path

from . import views

app_name = 'chatbot'
urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('close/', views.close, name='close'),
    path('guest/', views.guest, name='guest'),
    path('chat/', views.chat, name='chat'),
    path('chat/process_message/', views.process_message, name='process_message'),
    path('chat/provider_login/', views.provider_login, name='provider_login'),
]
