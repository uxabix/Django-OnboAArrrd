from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .decorators import user_has_hr_role


def home(request):
    return render(request, "accounts/home.html")


@login_required
def logged(request):
    return render(
        request,
        "accounts/logged.html",
        {"user_is_hr": user_has_hr_role(request.user)},
    )

