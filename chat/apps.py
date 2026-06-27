"""App configuration for the ``chat`` Django application."""

from django.apps import AppConfig


class ChatConfig(AppConfig):
    """Standard ``AppConfig`` for chat models and views."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "chat"
