"""Database-backed tests for ``User_tasks`` workflow properties."""

from datetime import timedelta

import pytest
from django.utils import timezone

from onboarding.models import Competency_paths, Task_status, Task_types, Tasks, User_tasks

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog_task(db):
    path = Competency_paths.objects.create(name="Path", description="D")
    task_type = Task_types.objects.create(task_type="Text")
    return Tasks.objects.create(
        path=path,
        task_type=task_type,
        title="Task 1",
        description="",
        path_order=1,
    )


def test_user_tasks_current_status_and_submission(student_user, catalog_task, mentor_user):
    user_task = User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        assigned_by=mentor_user,
        deadline=timezone.now().date() + timedelta(days=5),
    )
    status = Task_status.objects.create(
        user_task=user_task,
        new_status=Task_status.Status.DO_WERYFIKACJI,
    )
    assert user_task.latest_status.pk == status.pk
    assert user_task.current_status == Task_status.Status.DO_WERYFIKACJI
    assert user_task.is_submitted is True
    assert user_task.submission_date == status.change_date


def test_user_tasks_is_approaching_deadline(db, student_user, catalog_task):
    user_task = User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        deadline=timezone.now().date() + timedelta(days=2),
    )
    assert user_task.is_approaching_deadline is True


def test_user_tasks_deadline_state_on_track(db, student_user, catalog_task):
    user_task = User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        deadline=timezone.now().date() + timedelta(days=10),
    )
    assert user_task.deadline_state == "on_track"


def test_user_tasks_is_overdue_when_unsubmitted_and_past_deadline(
    db, student_user, catalog_task
):
    user_task = User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        deadline=timezone.now().date() - timedelta(days=1),
    )
    assert user_task.is_overdue is True


def test_user_tasks_current_status_defaults_to_do_zrobienia(
    db, student_user, catalog_task
):
    user_task = User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        deadline=timezone.now().date(),
    )
    assert user_task.current_status == Task_status.Status.DO_ZROBIENIA


def test_update_mentor_stars_on_status_update_to_completed(
    student_user, catalog_task, mentor_user
):
    mentor_user.stars = 0
    mentor_user.save(update_fields=["stars"])
    user_task = User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        assigned_by=mentor_user,
        deadline=timezone.now().date() + timedelta(days=1),
    )
    status = Task_status.objects.create(
        user_task=user_task,
        new_status=Task_status.Status.W_TRAKCIE,
    )
    status.new_status = Task_status.Status.UKONCZONE
    status.save()
    mentor_user.refresh_from_db()
    assert mentor_user.stars == 1
