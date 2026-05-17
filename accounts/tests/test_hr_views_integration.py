"""Integration tests for HR dashboard HTTP flows."""

import pytest
from django.urls import reverse

from accounts.models import CustomUser

pytestmark = pytest.mark.django_db


def test_hr_dashboard_accessible_for_hr_user(client, hr_user):
    client.force_login(hr_user)
    response = client.get(reverse("accounts:hr_dashboard"))
    assert response.status_code == 200
    assert "employees" in response.context


def test_hr_dashboard_forbidden_for_student(client, student_user):
    client.force_login(student_user)
    response = client.get(reverse("accounts:hr_dashboard"))
    assert response.status_code == 403


def test_hr_add_employee_creates_active_user_with_temporary_password(
    client, hr_user, student_role
):
    client.force_login(hr_user)
    response = client.post(
        reverse("accounts:hr_add_employee"),
        {
            "email": "new.hire@example.com",
            "first_name": "New",
            "last_name": "Hire",
            "role": student_role.pk,
        },
    )
    assert response.status_code == 302
    created = CustomUser.objects.get(email="new.hire@example.com")
    assert created.is_active is True
    assert created.password_is_user_chosen is False
    assert created.hr_temporary_password_plain


def test_hr_terminate_and_reactivate_employee(client, hr_user, student_user):
    client.force_login(hr_user)
    terminate_url = reverse("accounts:hr_terminate_employee", args=[student_user.pk])
    response = client.post(terminate_url)
    assert response.status_code == 302
    student_user.refresh_from_db()
    assert student_user.is_active is False
    assert student_user.status == CustomUser.UserStatus.INACTIVE

    reactivate_url = reverse("accounts:hr_reactivate_employee", args=[student_user.pk])
    response = client.post(reactivate_url)
    assert response.status_code == 302
    student_user.refresh_from_db()
    assert student_user.is_active is True
    assert student_user.status == CustomUser.UserStatus.ACTIVE


def test_hr_export_database_rejects_invalid_form(client, hr_user):
    client.force_login(hr_user)
    response = client.post(reverse("accounts:hr_export_database"), {})
    assert response.status_code == 302
    assert response.url.endswith(reverse("accounts:hr_dashboard"))
