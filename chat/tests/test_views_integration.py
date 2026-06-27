"""Integration tests for chat HTTP endpoints."""

import pytest
from django.urls import reverse

from chat.models import Messages
from chat.views import _display_name, _load_context

pytestmark = pytest.mark.django_db


def test_display_name_prefers_full_name(mentor_user):
    assert _display_name(mentor_user) == "Jan Mentor"


def test_load_context_task_scope_for_participants(mentor_user, student_user, assigned_user_task):
    kind, obj, title = _load_context(
        mentor_user,
        student_user,
        "task",
        str(assigned_user_task.pk),
    )
    assert kind == "task"
    assert obj.pk == assigned_user_task.pk
    assert title == assigned_user_task.task_id.title


def test_load_context_rejects_outsider(mentor_role, student_user, assigned_user_task):
    from accounts.models import CustomUser

    outsider = CustomUser.objects.create_user(
        email="outsider@example.com",
        password="pass12345",
        first_name="Out",
        last_name="Side",
        role=mentor_role,
    )
    kind, obj, title = _load_context(
        outsider,
        student_user,
        "task",
        str(assigned_user_task.pk),
    )
    assert (kind, obj, title) == (None, None, None)


def test_chat_inbox_renders_for_authenticated_user(client, student_user):
    client.force_login(student_user)
    response = client.get(reverse("chat:chat_inbox"))
    assert response.status_code == 200


def test_chat_student_alias_routes_to_inbox(client, student_user):
    client.force_login(student_user)
    response = client.get(reverse("chat:chat_student"))
    assert response.status_code == 200


def test_chat_updates_returns_new_messages(client, mentor_user, student_user):
    Messages.objects.create(
        sender=student_user,
        receiver=mentor_user,
        text="Hello mentor",
    )
    client.force_login(mentor_user)
    response = client.get(reverse("chat:chat_updates", args=[student_user.pk]))
    assert response.status_code == 200
    body = response.json()
    assert len(body["messages"]) == 1
    assert body["messages"][0]["text"] == "Hello mentor"
