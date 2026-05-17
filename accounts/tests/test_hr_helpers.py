"""Unit tests for private helpers in ``accounts.hr_views``."""

from types import SimpleNamespace

from accounts.hr_views import (
    _apply_hr_list_filters,
    _hr_can_change_role_for_target,
    _hr_can_manage_actor,
    _parse_hr_list_params,
    _preservation_dict,
)
from accounts.models import CustomUser


def _user(pk, *, role_name=None, superuser=False):
    role = SimpleNamespace(name=role_name) if role_name else None
    return SimpleNamespace(
        pk=pk,
        is_superuser=superuser,
        is_authenticated=True,
        role=role,
    )


def test_hr_can_manage_actor_blocks_self_and_elevated_targets():
    hr = _user(1, role_name="HR")
    other_hr = _user(2, role_name="HR")
    student = _user(3, role_name="Student")
    su = _user(4, superuser=True)

    assert _hr_can_manage_actor(hr, hr) is False
    assert _hr_can_manage_actor(hr, other_hr) is False
    assert _hr_can_manage_actor(hr, student) is True
    assert _hr_can_manage_actor(hr, su) is False
    assert _hr_can_manage_actor(su, hr) is True


def test_hr_can_change_role_for_target_allows_self_for_administrator():
    admin = _user(1, role_name="Administrator")
    assert _hr_can_change_role_for_target(admin, admin) is True


def test_parse_hr_list_params_normalizes_invalid_sort_and_page():
    parsed = _parse_hr_list_params(
        {"q": "  anna  ", "sort": "not-valid", "page": "0", "filter_role": "5"}
    )
    assert parsed["q"] == "anna"
    assert parsed["sort"] == "last_name"
    assert parsed["page"] == "1"
    assert parsed["role_id"] == 5


def test_apply_hr_list_filters_by_search_term(db, mentor_user, student_user):
    params = _parse_hr_list_params({"q": "anna"})
    qs = _apply_hr_list_filters(CustomUser.objects.all(), params)
    emails = set(qs.values_list("email", flat=True))
    assert student_user.email in emails
    assert mentor_user.email not in emails


def test_preservation_dict_includes_active_filters():
    params = _parse_hr_list_params({"q": "test", "sort": "email"})
    preserved = _preservation_dict(params, page_number=2)
    assert preserved["q"] == "test"
    assert preserved["sort"] == "email"
    assert preserved["page"] == "2"
