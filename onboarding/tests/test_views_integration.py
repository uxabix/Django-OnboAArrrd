"""Integration tests for student and mentor onboarding views."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from onboarding.models import Task_status, User_tasks

pytestmark = pytest.mark.django_db


def test_user_tasks_list_renders_for_student_with_assignment(
    client, student_user, assigned_user_task
):
    client.force_login(student_user)
    response = client.get(reverse("onboarding:user_tasks_list"))
    assert response.status_code == 200
    assert response.context["stats"]["total"] >= 1


def test_user_task_detail_requires_owner(client, mentor_user, assigned_user_task):
    client.force_login(mentor_user)
    response = client.get(
        reverse("onboarding:user_task_detail", args=[assigned_user_task.pk])
    )
    assert response.status_code == 404


def test_user_submit_task_creates_verification_status(client, student_user, assigned_user_task):
    client.force_login(student_user)
    url = reverse("onboarding:user_submit_task", args=[assigned_user_task.pk])
    response = client.post(url)
    assert response.status_code == 302
    assigned_user_task.refresh_from_db()
    assert assigned_user_task.current_status == Task_status.Status.DO_WERYFIKACJI


def test_user_submit_task_rejects_duplicate_submission(
    client, student_user, assigned_user_task
):
    Task_status.objects.create(
        user_task=assigned_user_task,
        new_status=Task_status.Status.DO_WERYFIKACJI,
    )
    client.force_login(student_user)
    url = reverse("onboarding:user_submit_task", args=[assigned_user_task.pk])
    response = client.post(url)
    assert response.status_code == 302
    assert assigned_user_task.statuses.count() == 1


def test_mentor_change_user_task_status_appends_history(
    client, mentor_user, student_user, assigned_user_task
):
    client.force_login(mentor_user)
    url = reverse(
        "onboarding:mentor_change_user_task_status",
        args=[assigned_user_task.pk],
    )
    response = client.post(url, {"new_status": Task_status.Status.UKONCZONE})
    assert response.status_code == 302
    latest = assigned_user_task.statuses.order_by("-task_status_id").first()
    assert latest.new_status == Task_status.Status.UKONCZONE


def test_mentor_change_user_task_status_denies_foreign_mentor(
    client, mentor_role, student_user, assigned_user_task
):
    from accounts.models import CustomUser

    other_mentor = CustomUser.objects.create_user(
        email="other.mentor@example.com",
        password="pass12345",
        first_name="Other",
        last_name="Mentor",
        role=mentor_role,
    )
    client.force_login(other_mentor)
    url = reverse(
        "onboarding:mentor_change_user_task_status",
        args=[assigned_user_task.pk],
    )
    response = client.post(url, {"new_status": Task_status.Status.UKONCZONE})
    assert response.status_code == 200
    assert assigned_user_task.statuses.count() == 0


def test_mentor_task_management_lists_mentee(client, mentor_user, student_user, assigned_user_task):
    client.force_login(mentor_user)
    response = client.get(
        reverse("onboarding:mentor_task_management", args=[student_user.pk])
    )
    assert response.status_code == 200
