#!/usr/bin/env python
"""Command-line entrypoint for Django management commands."""

import os
import sys


def main():
    """Parse ``sys.argv`` and delegate execution to Django's management utility.

    Raises:
        ImportError: When Django is not installed in the active environment.
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "OnboAArrrd.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
