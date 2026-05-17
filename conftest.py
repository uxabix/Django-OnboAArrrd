"""Shared pytest fixtures for app tests."""

import pytest

from accounts.models import CustomUser, Roles


@pytest.fixture
def mentor_role(db):
    return Roles.objects.create(name="Mentor", description="Mentor role")


@pytest.fixture
def student_role(db):
    return Roles.objects.create(name="Student", description="Student role")


@pytest.fixture
def hr_role(db):
    return Roles.objects.create(name="HR", description="HR role")


@pytest.fixture
def mentor_user(db, mentor_role):
    return CustomUser.objects.create_user(
        email="mentor@example.com",
        password="pass12345",
        first_name="Jan",
        last_name="Mentor",
        role=mentor_role,
    )


@pytest.fixture
def student_user(db, student_role, mentor_user):
    return CustomUser.objects.create_user(
        email="student@example.com",
        password="pass12345",
        first_name="Anna",
        last_name="Student",
        role=student_role,
        mentor=mentor_user,
    )


@pytest.fixture
def hr_user(db, hr_role):
    return CustomUser.objects.create_user(
        email="hr@example.com",
        password="pass12345",
        first_name="Helena",
        last_name="HR",
        role=hr_role,
    )


@pytest.fixture
def competency_path(db):
    from onboarding.models import Competency_paths

    return Competency_paths.objects.create(
        name="Integration Path",
        description="Path used in integration tests",
    )


@pytest.fixture
def catalog_task(db, competency_path):
    from onboarding.models import Task_types, Tasks

    task_type = Task_types.objects.create(task_type="Text")
    return Tasks.objects.create(
        path=competency_path,
        task_type=task_type,
        title="Integration task",
        description="Do the thing",
        path_order=1,
    )


@pytest.fixture
def assigned_user_task(db, student_user, mentor_user, catalog_task):
    from datetime import timedelta

    from django.utils import timezone

    from onboarding.models import User_tasks

    return User_tasks.objects.create(
        user_id=student_user,
        task_id=catalog_task,
        assigned_by=mentor_user,
        deadline=timezone.now().date() + timedelta(days=7),
    )
