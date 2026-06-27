"""Tests for ``accounts.admin`` display helpers."""

import pytest

from accounts.admin import CustomUserAdmin

pytestmark = pytest.mark.django_db
from accounts.models import CustomUser


def test_custom_user_admin_get_mentor_returns_linked_mentor(mentor_user, student_user):
    admin = CustomUserAdmin(model=CustomUser, admin_site=None)
    assert admin.get_mentor(student_user) is mentor_user
