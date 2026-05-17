"""Lightweight HTTP smoke tests for ``accounts.views``."""

import pytest
from django.urls import reverse


def test_home_renders_for_anonymous(client):
    response = client.get(reverse("accounts:home"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_logged_passes_hr_flag_for_hr_user(client, hr_role):
    from accounts.models import CustomUser

    user = CustomUser.objects.create_user(
        email="hr2@example.com",
        password="pass12345",
        first_name="H",
        last_name="R",
        role=hr_role,
    )
    client.force_login(user)
    response = client.get(reverse("accounts:logged"))
    assert response.status_code == 200
    assert response.context["user_can_access_hr"] is True


@pytest.mark.django_db
def test_logged_denies_hr_flag_for_student(client, student_user):
    client.force_login(student_user)
    response = client.get(reverse("accounts:logged"))
    assert response.status_code == 200
    assert response.context["user_can_access_hr"] is False
