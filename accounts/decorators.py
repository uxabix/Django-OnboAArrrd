from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def _role_name_lower(user):
    role = getattr(user, "role", None)
    if role is None or not role.name:
        return ""
    return role.name.strip().lower()


def user_has_hr_role(user):
    """Return True if the user's role record is HR (case-insensitive name match)."""
    return _role_name_lower(user) == "hr"


def user_is_administrator_role(user):
    """Non-superuser with Admin / Administrator role name."""
    if not getattr(user, "is_authenticated", False) or user.is_superuser:
        return False
    return _role_name_lower(user) in ("admin", "administrator")


def user_can_access_hr_panel(user):
    """Superuser, Administrator role, or HR role may open the HR panel."""
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    rn = _role_name_lower(user)
    return rn in ("hr", "admin", "administrator")


def hr_required(view_func):
    """Restrict view to users allowed to use the HR panel."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not user_can_access_hr_panel(request.user):
            return render(
                request,
                "accounts/hr_access_denied.html",
                status=403,
            )
        return view_func(request, *args, **kwargs)

    return _wrapped
