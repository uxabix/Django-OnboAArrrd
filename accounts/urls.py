from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # przykładowe ścieżki:
    path('', views.home, name='home'),
    path('accounts/logged/', views.logged, name='logged'),
    ]