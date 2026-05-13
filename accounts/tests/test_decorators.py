"""Unit tests for ``accounts.decorators`` role helper functions."""

from types import SimpleNamespace

import pytest

from accounts.decorators import (
    user_can_access_hr_panel,
    user_has_hr_role,
    user_is_administrator_role,
)


def _make_user(
    role_name=None,
    *,
    authenticated=True,
    superuser=False,
):
    """Build a lightweight user stand-in for permission unit tests.

    Args:
        role_name: Optional ``Roles.name`` string carried on ``user.role``.
        authenticated: ``user.is_authenticated`` flag.
        superuser: ``user.is_superuser`` flag.

    Returns:
        SimpleNamespace: Object compatible with decorator attribute access.
    """
    role = SimpleNamespace(name=role_name) if role_name is not None else None
    return SimpleNamespace(
        role=role,
        is_authenticated=authenticated,
        is_superuser=superuser,
    )


def test_user_has_hr_role_matches_case_insensitive_name():
    assert user_has_hr_role(_make_user("HR")) is True
    assert user_has_hr_role(_make_user("hr")) is True
    assert user_has_hr_role(_make_user("  Hr  ")) is True
    assert user_has_hr_role(_make_user("Mentor")) is False
    assert user_has_hr_role(_make_user(None)) is False


def test_user_is_administrator_role_requires_authenticated_non_superuser():
    assert user_is_administrator_role(_make_user("Admin")) is True
    assert user_is_administrator_role(_make_user("Administrator")) is True
    assert user_is_administrator_role(_make_user("administrator")) is True
    assert user_is_administrator_role(_make_user("Admin", superuser=True)) is False
    assert user_is_administrator_role(_make_user("Admin", authenticated=False)) is False


def test_user_can_access_hr_panel_allows_superuser_without_named_role():
    user = _make_user(None, authenticated=True, superuser=True)
    assert user_can_access_hr_panel(user) is True


@pytest.mark.parametrize(
    "role_name,expected",
    [
        ("HR", True),
        ("Admin", True),
        ("Administrator", True),
        ("Mentor", False),
    ],
)
def test_user_can_access_hr_panel_respects_named_roles(role_name, expected):
    user = _make_user(role_name, authenticated=True, superuser=False)
    assert user_can_access_hr_panel(user) is expected


def test_user_can_access_hr_panel_denies_unauthenticated_users():
    user = _make_user("HR", authenticated=False, superuser=False)
    assert user_can_access_hr_panel(user) is False
