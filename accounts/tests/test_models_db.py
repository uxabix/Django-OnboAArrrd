"""Database-backed tests for ``accounts.models``."""

import pytest

from accounts.models import CustomUser, Roles

pytestmark = pytest.mark.django_db


def test_custom_user_manager_rejects_empty_email():
    with pytest.raises(ValueError, match="Email"):
        CustomUser.objects.create_user(email="")


def test_custom_user_manager_sets_unusable_password_when_omitted(db, mentor_role):
    user = CustomUser.objects.create_user(
        email="nopass@example.com",
        first_name="A",
        last_name="B",
        role=mentor_role,
    )
    assert not user.has_usable_password()


def test_custom_user_manager_create_superuser_requires_password(db):
    with pytest.raises(ValueError, match="hasło"):
        CustomUser.objects.create_superuser(
            email="su@example.com",
            password=None,
            first_name="S",
            last_name="U",
        )


def test_custom_user_manager_create_superuser_persists_active_staff():
    user = CustomUser.objects.create_superuser(
        email="su@example.com",
        password="secret123",
        first_name="S",
        last_name="U",
    )
    assert user.is_superuser is True
    assert user.is_staff is True
    assert user.status == CustomUser.UserStatus.ACTIVE


def test_custom_user_get_stars_display():
    user = CustomUser(email="x@example.com", stars=3)
    assert user.get_stars_display() == "⭐" * 3


def test_custom_user_is_mentor_reflects_mentees(db, mentor_user, student_user):
    assert mentor_user.is_mentor is True
    assert student_user.is_mentor is False


def test_roles_str_persisted(db):
    role = Roles.objects.create(name="Admin", description="Site admin")
    assert str(role) == "Admin"
