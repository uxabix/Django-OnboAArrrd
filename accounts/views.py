from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import user_can_access_hr_panel
from .forms import apply_bootstrap_control_widgets
from .models import CustomUser


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
def user_profile(request, user_id=None):
    profile_user = request.user if user_id is None else get_object_or_404(
        CustomUser.objects.select_related("role", "mentor"),
        pk=user_id,
    )
    is_own_profile = profile_user.pk == request.user.pk

    from onboarding.models import (
        Task_status,
        User_badges,
        User_grade,
        User_paths,
        User_tasks,
    )

    user_tasks_qs = (
        User_tasks.objects.filter(user_id=profile_user)
        .select_related("task_id", "task_id__path", "assigned_by")
        .prefetch_related("statuses")
    )
    user_tasks = list(user_tasks_qs)
    total_tasks = len(user_tasks)
    completed_tasks = sum(
        1 for user_task in user_tasks if user_task.current_status == Task_status.Status.UKONCZONE
    )
    submitted_for_review_tasks = sum(
        1 for user_task in user_tasks if user_task.current_status == Task_status.Status.DO_WERYFIKACJI
    )
    in_progress_tasks = sum(
        1 for user_task in user_tasks if user_task.current_status == Task_status.Status.W_TRAKCIE
    )
    to_do_tasks = sum(
        1 for user_task in user_tasks if user_task.current_status == Task_status.Status.DO_ZROBIENIA
    )
    overdue_tasks = sum(1 for user_task in user_tasks if user_task.deadline_state == "overdue")

    mentees = list(profile_user.mentees.select_related("role", "mentor").order_by("first_name", "last_name", "email"))
    mentees_count = len(mentees)
    mentees_task_total = User_tasks.objects.filter(user_id__mentor=profile_user).count()
    mentees_completed_tasks = User_tasks.objects.filter(
        user_id__mentor=profile_user,
        statuses__new_status=Task_status.Status.UKONCZONE,
    ).distinct().count()

    context = {
        "profile_user": profile_user,
        "is_own_profile": is_own_profile,
        "mentor_name": (
            f"{profile_user.mentor.first_name} {profile_user.mentor.last_name}".strip() or profile_user.mentor.email
        ) if profile_user.mentor else None,
        "mentees": mentees,
        "mentees_count": mentees_count,
        "stats": {
            "stars": profile_user.stars,
            "paths_count": User_paths.objects.filter(user=profile_user).count(),
            "tasks_total": total_tasks,
            "tasks_completed": completed_tasks,
            "tasks_submitted_for_review": submitted_for_review_tasks,
            "tasks_in_progress": in_progress_tasks,
            "tasks_to_do": to_do_tasks,
            "tasks_overdue": overdue_tasks,
            "badges_count": User_badges.objects.filter(user=profile_user).count(),
            "reports_received_count": profile_user.reports_received.count(),
            "reports_generated_count": profile_user.reports_generated.count(),
            "grades_received_count": profile_user.reviewed_grades.count(),
            "grades_given_count": profile_user.reviewer_grades.count(),
            "avg_grade_received": profile_user.reviewed_grades.aggregate(models.Avg("rating"))["rating__avg"],
            "avg_grade_given": profile_user.reviewer_grades.aggregate(models.Avg("rating"))["rating__avg"],
            "mentees_count": mentees_count,
            "mentees_task_total": mentees_task_total,
            "mentees_tasks_completed": mentees_completed_tasks,
        },
    }
    return render(request, "accounts/user_profile.html", context)


@login_required
def mentor_ranking(request):
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

