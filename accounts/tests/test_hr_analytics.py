"""Tests for HR onboarding analytics helpers."""

from datetime import timedelta

import pytest
from django.utils import timezone

from accounts.hr_analytics import compute_hr_analytics, parse_hr_stats_period
from onboarding.models import Competency_paths, Task_status, User_paths, User_tasks

pytestmark = pytest.mark.django_db


def test_parse_hr_stats_period_defaults_to_last_30_days():
    today = timezone.now().date()
    date_from, date_to, display_from, display_to = parse_hr_stats_period("", "")
    assert date_to == today
    assert date_from == today - timedelta(days=30)
    assert display_from == date_from.isoformat()
    assert display_to == date_to.isoformat()


def test_parse_hr_stats_period_all_time():
    date_from, date_to, display_from, display_to = parse_hr_stats_period(
        "", "", apply_default=False, all_time=True
    )
    assert date_from is None
    assert date_to is None
    assert display_from == ""
    assert display_to == ""


def test_compute_hr_analytics_counts_assignments_and_timeliness(
    student_user, mentor_user, catalog_task, competency_path
):
    today = timezone.now().date()

    on_time_task = User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        assigned_by=mentor_user,
        deadline=today + timedelta(days=5),
    )
    Task_status.objects.create(
        user_task=on_time_task,
        new_status=Task_status.Status.DO_WERYFIKACJI,
        change_date=today,
    )

    late_task = User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        assigned_by=mentor_user,
        deadline=today - timedelta(days=3),
    )
    Task_status.objects.create(
        user_task=late_task,
        new_status=Task_status.Status.DO_WERYFIKACJI,
        change_date=today,
    )

    User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        assigned_by=mentor_user,
        deadline=today - timedelta(days=2),
    )

    User_paths.objects.create(
        user=student_user,
        path=competency_path,
        assigned_by=mentor_user,
    )

    stats = compute_hr_analytics(today - timedelta(days=1), today + timedelta(days=1))

    assert stats["tasks_total"] == 3
    assert stats["paths_total"] == 1
    assert stats["users_with_tasks"] == 1
    assert stats["users_with_paths"] == 1
    assert stats["avg_tasks_per_user"] == 3.0
    assert stats["avg_paths_per_user"] == 1.0
    assert stats["on_time_count"] == 1
    assert stats["late_count"] == 1
    assert stats["overdue_count"] == 1
    assert stats["not_on_time_count"] == 2
    assert stats["submitted_count"] == 2
    assert stats["open_count"] == 0


def test_compute_hr_analytics_respects_assignment_period(
    student_user, mentor_user, catalog_task
):
    today = timezone.now().date()
    old_task = User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        assigned_by=mentor_user,
        deadline=today + timedelta(days=3),
    )
    User_tasks.objects.filter(pk=old_task.pk).update(
        created_at=timezone.now() - timedelta(days=40)
    )

    recent_task = User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        assigned_by=mentor_user,
        deadline=today + timedelta(days=3),
    )

    stats = compute_hr_analytics(today - timedelta(days=7), today)
    assert stats["tasks_total"] == 1
    assert recent_task.pk != old_task.pk


def test_completion_days_clamped_when_submission_predates_assignment(
    student_user, mentor_user, catalog_task
):
    """Seeded/imported statuses may carry dates before assignment; metric stays >= 0."""
    today = timezone.now().date()
    user_task = User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        assigned_by=mentor_user,
        deadline=today + timedelta(days=5),
    )
    Task_status.objects.create(
        user_task=user_task,
        new_status=Task_status.Status.DO_WERYFIKACJI,
        change_date=today - timedelta(days=5),
    )

    stats = compute_hr_analytics(today - timedelta(days=1), today + timedelta(days=1))

    assert stats["submitted_count"] == 1
    assert stats["avg_completion_days"] == 0.0


def test_completion_days_uses_days_between_assignment_and_submission(
    student_user, mentor_user, catalog_task
):
    today = timezone.now().date()
    assigned_at = timezone.now() - timedelta(days=4)
    user_task = User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        assigned_by=mentor_user,
        deadline=today + timedelta(days=5),
    )
    User_tasks.objects.filter(pk=user_task.pk).update(created_at=assigned_at)
    Task_status.objects.create(
        user_task=user_task,
        new_status=Task_status.Status.DO_WERYFIKACJI,
        change_date=today,
    )

    stats = compute_hr_analytics(today - timedelta(days=10), today + timedelta(days=1))

    assert stats["avg_completion_days"] == 4.0


def test_hr_dashboard_includes_analytics_context(client, hr_user, assigned_user_task):
    from django.urls import reverse

    client.force_login(hr_user)
    response = client.get(reverse("accounts:hr_dashboard"))
    assert response.status_code == 200
    assert "hr_analytics" in response.context
    assert "stats_from" in response.context
    assert response.context["hr_analytics"]["tasks_total"] >= 1
