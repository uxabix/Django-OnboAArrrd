"""Tests for ``accounts.middleware.ForceInitialPasswordChangeMiddleware``."""

from unittest.mock import MagicMock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from accounts.middleware import ForceInitialPasswordChangeMiddleware
from accounts.models import CustomUser


@pytest.fixture
def rf():
    return RequestFactory()


def _run_middleware(request, user=None):
    if user is not None:
        request.user = user
    captured = {}

    def get_response(req):
        captured["request"] = req
        return HttpResponse("ok")

    middleware = ForceInitialPasswordChangeMiddleware(get_response)
    return middleware(request), captured


@pytest.mark.django_db
def test_middleware_passes_when_password_is_user_chosen(rf, mentor_user):
    mentor_user.password_is_user_chosen = True
    request = rf.get("/accounts/logged/")
    request.user = mentor_user
    response, _ = _run_middleware(request)
    assert response.content == b"ok"


@pytest.mark.django_db
def test_middleware_redirects_when_temporary_password_active(rf, mentor_user):
    mentor_user.password_is_user_chosen = False
    request = rf.get("/accounts/logged/")
    request.user = mentor_user
    response, _ = _run_middleware(request)
    assert response.status_code == 302
    assert response["Location"] == reverse("accounts:force_first_password_change")


@pytest.mark.django_db
def test_middleware_exempts_force_password_change_path(rf, mentor_user):
    mentor_user.password_is_user_chosen = False
    path = reverse("accounts:force_first_password_change")
    request = rf.get(path)
    request.user = mentor_user
    response, _ = _run_middleware(request)
    assert response.content == b"ok"


def test_middleware_ignores_anonymous_user(rf):
    request = rf.get("/accounts/logged/")
    request.user = AnonymousUser()
    response, _ = _run_middleware(request)
    assert response.content == b"ok"


@pytest.mark.django_db
def test_is_exempt_login_and_logout_paths(rf):
    middleware = ForceInitialPasswordChangeMiddleware(MagicMock())
    login_request = rf.get(reverse("login"))
    logout_request = rf.get(reverse("logout"))
    assert middleware._is_exempt(login_request) is True
    assert middleware._is_exempt(logout_request) is True


def test_is_exempt_static_and_media_paths(rf):
    middleware = ForceInitialPasswordChangeMiddleware(MagicMock())
    static_request = rf.get("/static/app.js")
    media_request = rf.get("/media/avatar.png")
    assert middleware._is_exempt(static_request) is True
    assert middleware._is_exempt(media_request) is True
