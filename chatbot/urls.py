from django.urls import path

from . import views

app_name = 'chatbot'
urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('guest/', views.guest, name='guest'),
    path('login/', views.login, name='login'),
]
