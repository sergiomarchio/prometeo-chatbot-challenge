from django.urls import path

from . import views

app_name = 'chatbot'
urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('logout/', views.logout, name='logout'),
    path('chat/', views.chat, name='chat'),
    path('chat/process_message/', views.process_message, name='process_message'),
]
