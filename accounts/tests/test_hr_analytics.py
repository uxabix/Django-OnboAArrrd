"""Tests for HR onboarding analytics helpers."""

from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.db.models import Count
from django.utils import timezone

from accounts.hr_analytics import (
    _mentor_index,
    _performance_index,
    build_mentor_ranking,
    compute_hr_analytics,
    parse_hr_stats_period,
)
from accounts.models import CustomUser
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


def test_compute_hr_analytics_picks_best_student_and_mentor(
    db, student_role, mentor_role, catalog_task, competency_path
):
    today = timezone.now().date()

    mentor_a = CustomUser.objects.create_user(
        email="mentor.a@example.com",
        password="pass12345",
        first_name="Adam",
        last_name="Mentor",
        role=mentor_role,
    )
    mentor_b = CustomUser.objects.create_user(
        email="mentor.b@example.com",
        password="pass12345",
        first_name="Beata",
        last_name="Mentor",
        role=mentor_role,
    )
    student_a = CustomUser.objects.create_user(
        email="student.a@example.com",
        password="pass12345",
        first_name="Ala",
        last_name="Student",
        role=student_role,
        mentor=mentor_a,
    )
    student_b = CustomUser.objects.create_user(
        email="student.b@example.com",
        password="pass12345",
        first_name="Bartek",
        last_name="Student",
        role=student_role,
        mentor=mentor_b,
    )

    good_task = User_tasks.objects.create(
        user_id=student_a,
        task_id=catalog_task,
        assigned_by=mentor_a,
        deadline=today + timedelta(days=5),
    )
    Task_status.objects.create(
        user_task=good_task,
        new_status=Task_status.Status.DO_WERYFIKACJI,
        change_date=today,
    )

    mixed_task = User_tasks.objects.create(
        user_id=student_b,
        task_id=catalog_task,
        assigned_by=mentor_b,
        deadline=today - timedelta(days=2),
    )
    Task_status.objects.create(
        user_task=mixed_task,
        new_status=Task_status.Status.DO_WERYFIKACJI,
        change_date=today,
    )
    User_tasks.objects.create(
        user_id=student_b,
        task_id=catalog_task,
        assigned_by=mentor_b,
        deadline=today - timedelta(days=1),
    )

    User_paths.objects.create(user=student_a, path=competency_path, assigned_by=mentor_a)

    stats = compute_hr_analytics(today - timedelta(days=1), today + timedelta(days=1))

    assert stats["best_student"]["user_id"] == student_a.pk
    assert stats["best_student"]["score"] == 100.0
    assert stats["best_mentor"]["user_id"] == mentor_a.pk
    assert stats["best_mentor"]["score"] == 100.0
    assert stats["best_mentor"]["students_count"] == 1
    assert stats["best_mentor"]["paths_total"] == 1
    assert stats["best_mentor"]["stars"] == 0


def test_performance_and_mentor_index_helpers():
    student_stats = {
        "tasks_total": 4,
        "on_time": 3,
        "late": 1,
        "overdue": 0,
        "on_track": 0,
        "approaching": 0,
        "paths_total": 0,
        "student_ids": set(),
    }
    mentor_stats = {
        **student_stats,
        "paths_total": 2,
        "student_ids": {1, 2, 3},
        "user": SimpleNamespace(stars=0),
    }

    assert _performance_index(student_stats) == 83.8
    assert _mentor_index(mentor_stats) == 96.3

    mentor_stats["user"] = SimpleNamespace(stars=4)
    assert _mentor_index(mentor_stats) == 100.0


def test_mentor_ranking_uses_stars_as_tiebreaker(
    db, mentor_role, student_role, catalog_task
):
    today = timezone.now().date()
    mentor_low = CustomUser.objects.create_user(
        email="mentor.low@example.com",
        password="pass12345",
        role=mentor_role,
        stars=0,
    )
    mentor_high = CustomUser.objects.create_user(
        email="mentor.high@example.com",
        password="pass12345",
        role=mentor_role,
        stars=5,
    )
    student = CustomUser.objects.create_user(
        email="student.tie@example.com",
        password="pass12345",
        role=student_role,
        mentor=mentor_low,
    )

    for mentor in (mentor_low, mentor_high):
        user_task = User_tasks.objects.create(
            user_id=student,
            task_id=catalog_task,
            assigned_by=mentor,
            deadline=today + timedelta(days=3),
        )
        Task_status.objects.create(
            user_task=user_task,
            new_status=Task_status.Status.DO_WERYFIKACJI,
            change_date=today,
        )

    stats = compute_hr_analytics(today - timedelta(days=1), today + timedelta(days=1))
    assert stats["best_mentor"]["user_id"] == mentor_high.pk
    assert stats["best_mentor"]["stars"] == 5


def test_build_mentor_ranking_sorts_by_selected_metric(
    db, mentor_role, student_role, catalog_task
):
    today = timezone.now().date()
    mentor_stars = CustomUser.objects.create_user(
        email="mentor.stars@example.com",
        password="pass12345",
        role=mentor_role,
        stars=10,
    )
    mentor_active = CustomUser.objects.create_user(
        email="mentor.active@example.com",
        password="pass12345",
        role=mentor_role,
        stars=1,
    )
    student = CustomUser.objects.create_user(
        email="student.rank@example.com",
        password="pass12345",
        role=student_role,
        mentor=mentor_active,
    )

    user_task = User_tasks.objects.create(
        user_id=student,
        task_id=catalog_task,
        assigned_by=mentor_active,
        deadline=today + timedelta(days=4),
    )
    Task_status.objects.create(
        user_task=user_task,
        new_status=Task_status.Status.DO_WERYFIKACJI,
        change_date=today,
    )

    mentors = list(
        CustomUser.objects.filter(pk__in=[mentor_stars.pk, mentor_active.pk]).annotate(
            mentees_count=Count("mentees")
        )
    )

    by_stars, _ = build_mentor_ranking(
        mentors, metric="stars", date_from=today - timedelta(days=1), date_to=today + timedelta(days=1)
    )
    assert by_stars[0]["mentor"].pk == mentor_stars.pk

    by_hr, _ = build_mentor_ranking(
        mentors, metric="hr_index", date_from=today - timedelta(days=1), date_to=today + timedelta(days=1)
    )
    assert by_hr[0]["mentor"].pk == mentor_active.pk


def test_hr_dashboard_includes_analytics_context(client, hr_user, assigned_user_task):
    from django.urls import reverse

    client.force_login(hr_user)
    response = client.get(reverse("accounts:hr_dashboard"))
    assert response.status_code == 200
    assert "hr_analytics" in response.context
    assert "stats_from" in response.context
    assert response.context["hr_analytics"]["tasks_total"] >= 1
