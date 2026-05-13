"""Role-aware decorators used by account and HR views."""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def _role_name_lower(user):
    """Return the lowercased role label for the given user.

    Args:
        user: ``CustomUser`` instance (may be anonymous).

    Returns:
        str: Normalized role name or an empty string when undefined.
    """
    role = getattr(user, "role", None)
    if role is None or not role.name:
        return ""
    return role.name.strip().lower()


def user_has_hr_role(user):
    """Return whether the user's role record matches HR (case-insensitive).

    Args:
        user: Authenticated ``CustomUser``.

    Returns:
        bool: ``True`` when the role name equals ``hr``.
    """
    return _role_name_lower(user) == "hr"


def user_is_administrator_role(user):
    """Detect non-superuser accounts with administrator privileges.

    Args:
        user: ``CustomUser`` under test.

    Returns:
        bool: ``True`` for ``admin`` / ``administrator`` role names.
    """
    if not getattr(user, "is_authenticated", False) or user.is_superuser:
        return False
    return _role_name_lower(user) in ("admin", "administrator")


def user_can_access_hr_panel(user):
    """Return whether the user may open HR dashboard URLs.

    Args:
        user: ``CustomUser`` instance.

    Returns:
        bool: ``True`` for superusers, HR, or administrator roles.
    """
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    rn = _role_name_lower(user)
    return rn in ("hr", "admin", "administrator")


def hr_required(view_func):
    """Decorator enforcing HR panel access rules before running a view.

    Args:
        view_func: Django view callable.

    Returns:
        Callable: Wrapped view that returns ``403`` when access is denied.
    """

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
