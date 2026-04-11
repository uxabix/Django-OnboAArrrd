from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .decorators import hr_required
from .forms import HrAddEmployeeForm, HrChangeRoleForm, mentor_student_roles_queryset

CustomUserModel = get_user_model()


def _clear_mentor_links(user):
    """Detach mentees when mentor is demoted or terminated."""
    CustomUserModel.objects.filter(mentor=user).update(mentor=None)


def _hr_can_manage_actor(actor, target):
    """HR may not manage superusers, other HR accounts, or themselves (for risky actions)."""
    if target.is_superuser:
        return False
    tr = getattr(target, "role", None)
    if tr and tr.name and tr.name.strip().lower() == "hr":
        return False
    if target.pk == actor.pk:
        return False
    return True


@hr_required
def hr_dashboard(request):
    """List all employees with core fields; actions only where allowed."""
    users = list(
        CustomUserModel.objects.all()
        .select_related("role", "mentor")
        .order_by("last_name", "first_name", "email")
    )
    manageable_ids = {u.pk for u in users if _hr_can_manage_actor(request.user, u)}
    assignable_roles = list(mentor_student_roles_queryset())
    return render(
        request,
        "accounts/hr_dashboard.html",
        {
            "employees": users,
            "assignable_roles": assignable_roles,
            "manageable_ids": manageable_ids,
        },
    )


@hr_required
@require_http_methods(["GET", "POST"])
def hr_add_employee(request):
    """Create a new Mentor or Student account."""
    if request.method == "POST":
        form = HrAddEmployeeForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            role = data["role"]
            mentor = data["mentor"] if role.name.strip().lower() == "student" else None
            user = CustomUserModel.objects.create_user(
                email=data["email"],
                password=data["password1"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=role,
                mentor=mentor,
                status=CustomUserModel.UserStatus.ACTIVE,
            )
            user.is_active = True
            user.save(update_fields=["is_active"])
            messages.success(request, f"Dodano pracownika: {user.email}.")
            return redirect("accounts:hr_dashboard")
    else:
        form = HrAddEmployeeForm()
    return render(request, "accounts/hr_add_employee.html", {"form": form})


@hr_required
@require_http_methods(["POST"])
def hr_terminate_employee(request, user_id):
    """Soft-terminate: deactivate account and clear mentee links."""
    target = get_object_or_404(CustomUserModel, pk=user_id)
    if not _hr_can_manage_actor(request.user, target):
        messages.error(request, "Nie możesz zwolnić tego użytkownika.")
        return redirect("accounts:hr_dashboard")
    _clear_mentor_links(target)
    target.mentor = None
    target.status = CustomUserModel.UserStatus.INACTIVE
    target.is_active = False
    target.save(update_fields=["mentor", "status", "is_active"])
    messages.success(request, f"Pracownik {target.email} został zwolniony (konto wyłączone).")
    return redirect("accounts:hr_dashboard")


@hr_required
@require_http_methods(["POST"])
def hr_change_role(request, user_id):
    """Set role to Mentor or Student only; demoting a mentor clears mentees."""
    target = get_object_or_404(CustomUserModel, pk=user_id)
    if not _hr_can_manage_actor(request.user, target):
        messages.error(request, "Nie możesz zmienić roli tego użytkownika.")
        return redirect("accounts:hr_dashboard")
    form = HrChangeRoleForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Nieprawidłowe dane formularza roli.")
        return redirect("accounts:hr_dashboard")
    new_role = form.cleaned_data["role"]
    old_name = (target.role.name or "").strip().lower() if target.role else ""
    new_name = new_role.name.strip().lower()
    with transaction.atomic():
        if old_name == "mentor" and new_name == "student":
            _clear_mentor_links(target)
        target.role = new_role
        if new_name != "student":
            target.mentor = None
        target.save(update_fields=["role", "mentor"])
    messages.success(
        request,
        f"Zaktualizowano rolę użytkownika {target.email}.",
    )
    return redirect("accounts:hr_dashboard")
