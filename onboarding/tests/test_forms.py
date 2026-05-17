"""Tests for ``onboarding.forms`` queryset filtering."""

import pytest

pytestmark = pytest.mark.django_db

from onboarding.forms import UserPathForm, UserTaskForm
from onboarding.models import Competency_paths, Task_types, Tasks


@pytest.fixture
def seeded_catalog(db):
    path_a = Competency_paths.objects.create(name="Alpha Path", description="Alpha description")
    path_b = Competency_paths.objects.create(name="Beta Path", description="Other")
    task_type = Task_types.objects.create(task_type="Text")
    task_alpha = Tasks.objects.create(
        path=path_a,
        task_type=task_type,
        title="Alpha task",
        description="Do alpha",
        path_order=1,
    )
    Tasks.objects.create(
        path=path_b,
        task_type=task_type,
        title="Beta task",
        description="Do beta",
        path_order=1,
    )
    return path_a, task_alpha


def test_user_task_form_filters_by_search(seeded_catalog):
    _, task_alpha = seeded_catalog
    form = UserTaskForm(task_search="alpha")
    ids = list(form.fields["task_id"].queryset.values_list("pk", flat=True))
    assert ids == [task_alpha.pk]


def test_user_path_form_filters_by_search(seeded_catalog):
    path_a, _ = seeded_catalog
    form = UserPathForm(path_search="alpha")
    ids = list(form.fields["path"].queryset.values_list("pk", flat=True))
    assert ids == [path_a.pk]


def test_user_path_form_label_from_instance_truncates_description(seeded_catalog):
    path_a, _ = seeded_catalog
    form = UserPathForm()
    label = form.fields["path"].label_from_instance(path_a)
    assert label.startswith("Alpha Path - ")
    assert label.endswith("...")
