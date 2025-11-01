"""
ASGI config for OnboAArrrd project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter

import chat.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OnboAArrrd.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # "websocket": URLRouter(
    #
    # ),
})
