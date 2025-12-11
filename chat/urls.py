from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    # przykładowe ścieżki:
    path('', views.chat, name='chat'),
    ]