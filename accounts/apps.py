"""App configuration hook for the ``accounts`` Django application."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Metadata container pointing Django to the ``accounts`` package."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
