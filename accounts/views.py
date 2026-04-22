from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.shortcuts import redirect, render

from .decorators import user_can_access_hr_panel
from .forms import apply_bootstrap_control_widgets


def home(request):
    return render(request, "accounts/home.html")


@login_required
def logged(request):
    return render(
        request,
        "accounts/logged.html",
        {"user_can_access_hr": user_can_access_hr_panel(request.user)},
    )


@login_required
def mentor_ranking(request):
    from .models import CustomUser
    from django.core.paginator import Paginator
    mentors = CustomUser.objects.filter(
    role__name='Mentor'
    ).order_by('-stars').distinct()
    paginator = Paginator(mentors, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'accounts/mentor_ranking.html', {'page_obj': page_obj})


@login_required
def force_first_password_change(request):
    """Block app usage until the user replaces an HR-issued temporary password."""
    user = request.user
    if getattr(user, "password_is_user_chosen", True):
        return redirect(settings.LOGIN_REDIRECT_URL or "/accounts/logged/")
    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            user.password_is_user_chosen = True
            user.hr_temporary_password_plain = ""
            user.save(update_fields=["password_is_user_chosen", "hr_temporary_password_plain"])
            update_session_auth_hash(request, user)
            messages.success(request, "Hasło zostało ustawione. Możesz korzystać z platformy.")
            return redirect(settings.LOGIN_REDIRECT_URL or "/accounts/logged/")
    else:
        form = SetPasswordForm(user)
    apply_bootstrap_control_widgets(form)
    return render(
        request,
        "accounts/force_first_password_change.html",
        {"form": form},
    )

