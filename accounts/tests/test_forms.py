"""Tests for ``accounts.forms`` validation and helpers."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.forms import (
    HrAddEmployeeForm,
    HrChangeEmailForm,
    HrChangeMentorForm,
    HrDbExportForm,
    HrDbImportForm,
    apply_bootstrap_control_widgets,
)
from accounts.models import CustomUser
from django import forms


class _DummyForm(forms.Form):
    name = forms.CharField()


def test_apply_bootstrap_control_widgets_adds_class():
    form = _DummyForm()
    apply_bootstrap_control_widgets(form)
    assert form.fields["name"].widget.attrs["class"] == "form-control"


@pytest.mark.django_db
def test_hr_add_employee_rejects_duplicate_email(mentor_role, student_role, mentor_user):
    form = HrAddEmployeeForm(
        data={
            "email": mentor_user.email.upper(),
            "first_name": "X",
            "last_name": "Y",
            "role": student_role.pk,
        }
    )
    assert form.is_valid() is False
    assert "email" in form.errors


@pytest.mark.django_db
def test_hr_add_employee_rejects_mentor_for_non_student(mentor_role, mentor_user):
    form = HrAddEmployeeForm(
        data={
            "email": "new@example.com",
            "first_name": "X",
            "last_name": "Y",
            "role": mentor_role.pk,
            "mentor": mentor_user.pk,
        }
    )
    assert form.is_valid() is False
    assert "mentor" in form.errors


@pytest.mark.django_db
def test_hr_change_email_allows_same_user_pk(mentor_user):
    form = HrChangeEmailForm(
        data={"email": mentor_user.email},
        edited_user_pk=mentor_user.pk,
    )
    assert form.is_valid() is True


@pytest.mark.django_db
def test_hr_change_email_rejects_other_users_email(mentor_user, student_user):
    form = HrChangeEmailForm(
        data={"email": student_user.email},
        edited_user_pk=mentor_user.pk,
    )
    assert form.is_valid() is False


@pytest.mark.django_db
def test_hr_change_mentor_rejects_non_student_target(mentor_user, student_role):
    form = HrChangeMentorForm(
        data={"mentor": ""},
        edited_user=mentor_user,
    )
    assert form.is_valid() is False


@pytest.mark.django_db
def test_hr_change_mentor_rejects_self_assignment(student_user, mentor_user):
    form = HrChangeMentorForm(
        data={"mentor": student_user.pk},
        edited_user=student_user,
    )
    assert form.is_valid() is False
    assert "mentor" in form.errors


def test_hr_db_export_parse_ids_and_validation():
    form = HrDbExportForm(
        data={
            "export_format": "json",
            "data_scope": "users_only",
            "only_selected": True,
            "selected_user_ids": "1, 2, 2",
            "selected_task_ids": "",
        }
    )
    assert form.is_valid() is True
    assert form.cleaned_data["selected_user_ids_list"] == [1, 2]


def test_hr_db_export_rejects_full_db_with_only_selected_flag():
    form = HrDbExportForm(
        data={
            "export_format": "json",
            "data_scope": "full_db",
            "only_selected": True,
            "selected_user_ids": "1",
            "selected_task_ids": "",
        }
    )
    assert form.is_valid() is False


def test_hr_db_export_rejects_non_numeric_ids():
    form = HrDbExportForm(
        data={
            "export_format": "json",
            "data_scope": "users_only",
            "only_selected": True,
            "selected_user_ids": "1,abc",
            "selected_task_ids": "",
        }
    )
    assert form.is_valid() is False


def test_hr_db_export_build_filename():
    form = HrDbExportForm(
        data={
            "export_format": "yaml",
            "data_scope": "full_db",
            "only_selected": False,
        }
    )
    assert form.is_valid() is True
    name = form.build_filename()
    assert name.startswith("db_export_full_db_")
    assert name.endswith(".yaml")


def test_hr_db_import_rejects_unknown_extension():
    upload = SimpleUploadedFile("dump.txt", b"data")
    form = HrDbImportForm(data={"overwrite_existing": False}, files={"data_file": upload})
    assert form.is_valid() is False
    assert "data_file" in form.errors


@pytest.mark.django_db
def test_hr_db_import_accepts_json():
    upload = SimpleUploadedFile("dump.json", b"[]")
    form = HrDbImportForm(data={"overwrite_existing": True}, files={"data_file": upload})
    assert form.is_valid() is True
