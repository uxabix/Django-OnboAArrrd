"""WSGI entrypoint for traditional synchronous Django deployments."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OnboAArrrd.settings")

application = get_wsgi_application()
