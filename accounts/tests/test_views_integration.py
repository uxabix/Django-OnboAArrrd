"""Integration tests for public account views."""

import pytest
from django.urls import reverse

from accounts.models import CustomUser

pytestmark = pytest.mark.django_db


def test_user_search_suggest_requires_minimum_query_length(client, mentor_user):
    client.force_login(mentor_user)
    response = client.get(reverse("accounts:user_search_suggest"), {"q": "a"})
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_user_search_suggest_returns_matches(client, mentor_user, student_user):
    client.force_login(mentor_user)
    response = client.get(reverse("accounts:user_search_suggest"), {"q": "anna"})
    assert response.status_code == 200
    payload = response.json()["results"]
    assert any(item["email"] == student_user.email for item in payload)


def test_user_profile_shows_own_tasks_summary(client, student_user, assigned_user_task):
    client.force_login(student_user)
    response = client.get(reverse("accounts:user_profile"))
    assert response.status_code == 200
    assert response.context["stats"]["tasks_total"] >= 1


def test_mentor_ranking_lists_mentors(client, mentor_user):
    client.force_login(mentor_user)
    response = client.get(reverse("accounts:mentor_ranking"))
    assert response.status_code == 200
    assert response.context["page_obj"].paginator.count >= 1
    assert response.context["metric"] == "stars"


def test_mentor_ranking_supports_hr_index_metric(client, mentor_user, assigned_user_task):
    client.force_login(mentor_user)
    response = client.get(reverse("accounts:mentor_ranking"), {"metric": "hr_index"})
    assert response.status_code == 200
    assert response.context["metric"] == "hr_index"
    rows = list(response.context["page_obj"])
    assert rows
    assert rows[0]["hr_index"] is not None or rows[0]["tasks_assigned"] == 0


def test_mentor_ranking_preserves_metric_in_pagination_query(client, mentor_user):
    client.force_login(mentor_user)
    response = client.get(
        reverse("accounts:mentor_ranking"),
        {"metric": "tasks_assigned", "stats_from": "2020-01-01", "stats_to": "2099-12-31"},
    )
    assert response.status_code == 200
    assert "metric=tasks_assigned" in response.context["querystring_no_page"]
    assert "stats_from=2020-01-01" in response.context["querystring_no_page"]


def test_force_first_password_change_get_for_temporary_account(client, hr_user):
    hr_user.password_is_user_chosen = False
    hr_user.save(update_fields=["password_is_user_chosen"])
    client.force_login(hr_user)
    response = client.get(reverse("accounts:force_first_password_change"))
    assert response.status_code == 200
    assert "form" in response.context


def test_force_first_password_change_post_sets_user_password(client, hr_user):
    hr_user.password_is_user_chosen = False
    hr_user.hr_temporary_password_plain = "TempPass123!"
    hr_user.save(update_fields=["password_is_user_chosen", "hr_temporary_password_plain"])
    client.force_login(hr_user)
    response = client.post(
        reverse("accounts:force_first_password_change"),
        {
            "new_password1": "NewSecurePass123!",
            "new_password2": "NewSecurePass123!",
        },
    )
    assert response.status_code == 302
    hr_user.refresh_from_db()
    assert hr_user.password_is_user_chosen is True
    assert hr_user.hr_temporary_password_plain == ""
    assert hr_user.check_password("NewSecurePass123!")
