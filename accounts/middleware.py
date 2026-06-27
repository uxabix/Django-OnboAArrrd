from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class ForceInitialPasswordChangeMiddleware:
    """Force password rotation for accounts with HR-issued temporary passwords.

    Authenticated users whose ``password_is_user_chosen`` flag is ``False`` are
    redirected to ``accounts:force_first_password_change`` unless the request
    targets exempt authentication or static/media paths.

    Attributes:
        get_response: Django one-shot callable injected by the framework.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Invoke the middleware for a single request/response cycle.

        Args:
            request: Current ``HttpRequest``.

        Returns:
            HttpResponse: Either a redirect or the downstream response.
        """
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            if not getattr(user, "password_is_user_chosen", True):
                if not self._is_exempt(request):
                    return redirect(reverse("accounts:force_first_password_change"))
        return self.get_response(request)

    def _is_exempt(self, request):
        """Return ``True`` when password enforcement should not run.

        Args:
            request: Current ``HttpRequest``.

        Returns:
            bool: Whether the path is whitelisted.
        """
        path = request.path
        try:
            if path == reverse("accounts:force_first_password_change"):
                return True
            if path == reverse("logout"):
                return True
            if path == reverse("login"):
                return True
        except Exception:
            pass
        static_url = getattr(settings, "STATIC_URL", "/static/") or "/static/"
        if static_url and path.startswith(static_url):
            return True
        media_url = getattr(settings, "MEDIA_URL", "/media/") or "/media/"
        if media_url and path.startswith(media_url):
            return True
        return False
