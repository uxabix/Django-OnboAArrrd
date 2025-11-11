from django.urls import path
from . import views

urlpatterns = [
    # przykładowe ścieżki:
    path('', views.home, name='home')
    ]