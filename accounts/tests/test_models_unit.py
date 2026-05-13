"""Lightweight model tests that do not require database migrations."""

from accounts.models import Roles


def test_roles_str_uses_name_without_persisting():
    """Unsaved ``Roles`` instances should still render a stable ``__str__``."""
    role = Roles(name="Student", description="Learner access")
    assert str(role) == "Student"
