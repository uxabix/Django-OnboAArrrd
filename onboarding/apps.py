"""App configuration for the ``onboarding`` Django application."""

from django.apps import AppConfig


class OnboardingConfig(AppConfig):
    """Standard ``AppConfig`` pointing to the onboarding package."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "onboarding"
