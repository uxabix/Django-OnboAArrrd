from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class ForceInitialPasswordChangeMiddleware:
    """
    Users created or reset by HR must set their own password before using the app.
    Exempt only the forced-change view, logout, login, and static/media paths.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            if not getattr(user, "password_is_user_chosen", True):
                if not self._is_exempt(request):
                    return redirect(reverse("accounts:force_first_password_change"))
        return self.get_response(request)

    def _is_exempt(self, request):
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
