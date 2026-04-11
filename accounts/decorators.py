from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def user_has_hr_role(user):
    """Return True if the user's role record is HR (case-insensitive name match)."""
    role = getattr(user, "role", None)
    if role is None or not role.name:
        return False
    return role.name.strip().lower() == "hr"


def hr_required(view_func):
    """Restrict view to authenticated users whose Roles.name is HR."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not user_has_hr_role(request.user):
            return render(
                request,
                "accounts/hr_access_denied.html",
                status=403,
            )
        return view_func(request, *args, **kwargs)

    return _wrapped
