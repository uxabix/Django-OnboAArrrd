"""Tests for ``onboarding.admin`` display helpers."""

from onboarding.admin import BadgesAdmin
from onboarding.models import Badges


def test_badges_admin_icon_tag_without_icon():
    admin = BadgesAdmin(model=Badges, admin_site=None)
    badge = Badges(name="No icon", points=1, description="")
    assert admin.icon_tag(badge) == "-"
