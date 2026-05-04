import secrets
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods

from .decorators import hr_required, user_is_administrator_role
from .forms import (
    HrAddEmployeeForm,
    HrChangeEmailForm,
    HrChangeMentorForm,
    HrChangeRoleForm,
    apply_bootstrap_control_widgets,
    mentor_student_roles_queryset,
)
from .models import Roles

CustomUserModel = get_user_model()

# Query params preserved across POST actions (filters, search, sort, page).
# filter_role = role PK filter (must not clash with POST field "role" on change-role form)
_HR_LIST_PARAMS = ("q", "filter_role", "created_from", "created_to", "sort", "page")

# Whitelisted ordering keys -> ORM order_by fields
_HR_SORT_FIELDS = {
    "last_name": ("last_name", "first_name", "email"),
    "-last_name": ("-last_name", "-first_name", "-email"),
    "email": ("email",),
    "-email": ("-email",),
    "created_at": ("created_at", "email"),
    "-created_at": ("-created_at", "-email"),
    "role": ("role__name", "last_name", "first_name"),
    "-role": ("-role__name", "last_name", "first_name"),
}

_HR_PAGE_SIZE = 15


def _generate_hr_temporary_password():
    """Cryptographically strong one-time password for HR handoff (stored as plain text per product rules)."""
    return secrets.token_urlsafe(16)


def _clear_mentor_links(user):
    """Detach mentees when mentor is demoted or terminated."""
    CustomUserModel.objects.filter(mentor=user).update(mentor=None)


def _role_name_lower(role):
    if not role or not role.name:
        return ""
    return role.name.strip().lower()


def _hr_can_manage_actor(actor, target):
    """
    Terminate, reactivate, role change, HR temporary password reset for another user.
    Superuser: any user except self. Administrator role: any non-superuser except self.
    Plain HR: not superuser, not HR/Admin roles, not self.
    """
    if actor.pk == target.pk:
        return False
    if target.is_superuser and not actor.is_superuser:
        return False
    if actor.is_superuser:
        return True
    if user_is_administrator_role(actor):
        return True
    rn = _role_name_lower(getattr(target, "role", None))
    if rn in ("hr", "admin", "administrator"):
        return False
    return True


def _hr_can_change_role_for_target(actor, target):
    """
    Role change permission.
    Superuser / Administrator can also change own role from HR panel.
    """
    if actor.pk == target.pk:
        return actor.is_superuser or user_is_administrator_role(actor)
    return _hr_can_manage_actor(actor, target)


def _redirect_hr_dashboard(request):
    """After POST, return to the list with the same filters (internal query only)."""
    params = {}
    for key in _HR_LIST_PARAMS:
        v = (request.POST.get(key) or "").strip()
        if v:
            params[key] = v
    base = reverse("accounts:hr_dashboard")
    if params:
        return redirect(f"{base}?{urlencode(params)}")
    return redirect(base)


def _parse_hr_list_params(request_get):
    """Read and sanitize GET parameters for the employee list."""
    q = (request_get.get("q") or "").strip()[:200]
    role_raw = (request_get.get("filter_role") or "").strip()
    role_id = None
    if role_raw.isdigit():
        role_id = int(role_raw)
    created_from = (request_get.get("created_from") or "").strip()
    created_to = (request_get.get("created_to") or "").strip()
    sort = (request_get.get("sort") or "last_name").strip()
    if sort not in _HR_SORT_FIELDS:
        sort = "last_name"
    page = request_get.get("page") or "1"
    if not str(page).isdigit() or int(page) < 1:
        page = "1"
    return {
        "q": q,
        "filter_role": str(role_id) if role_id is not None else "",
        "role_id": role_id,
        "created_from": created_from,
        "created_to": created_to,
        "sort": sort,
        "page": page,
    }


def _apply_hr_list_filters(qs, p):
    """Apply search, role, and created_at range filters."""
    if p["q"]:
        term = p["q"]
        qs = qs.filter(
            Q(first_name__icontains=term)
            | Q(last_name__icontains=term)
            | Q(email__icontains=term)
        )
    if p["role_id"] is not None:
        qs = qs.filter(role_id=p["role_id"])
    df = parse_date(p["created_from"])
    if df:
        qs = qs.filter(created_at__date__gte=df)
    dt = parse_date(p["created_to"])
    if dt:
        qs = qs.filter(created_at__date__lte=dt)
    return qs


def _preservation_dict(p, page_number):
    """Hidden-field payload so POST actions keep list state."""
    out = {
        "q": p["q"],
        "filter_role": p["filter_role"],
        "created_from": p["created_from"],
        "created_to": p["created_to"],
        "sort": p["sort"],
        "page": str(page_number),
    }
    return out


def _querystring_except_page(request_get):
    """Build query string for pagination links (exclude page)."""
    mutable = request_get.copy()
    if "page" in mutable:
        del mutable["page"]
    return mutable.urlencode()


@hr_required
def hr_dashboard(request):
    """Paginated employee list with search, filters, and sort."""
    p = _parse_hr_list_params(request.GET)
    qs = CustomUserModel.objects.all().select_related("role", "mentor")
    qs = _apply_hr_list_filters(qs, p)
    qs = qs.order_by(*_HR_SORT_FIELDS[p["sort"]])

    paginator = Paginator(qs, _HR_PAGE_SIZE)
    page_obj = paginator.get_page(p["page"])

    preservation = _preservation_dict(p, page_obj.number)
    manageable_ids = {
        u.pk for u in page_obj.object_list if _hr_can_manage_actor(request.user, u)
    }
    role_manageable_ids = {
        u.pk for u in page_obj.object_list if _hr_can_change_role_for_target(request.user, u)
    }
    assignable_roles = list(mentor_student_roles_queryset())
    all_roles = list(Roles.objects.all().order_by("name"))
    mentor_candidates = list(
        CustomUserModel.objects.filter(role__name__iexact="Mentor")
        .order_by("first_name", "last_name", "email")
    )
    querystring_no_page = _querystring_except_page(request.GET)

    return render(
        request,
        "accounts/hr_dashboard.html",
        {
            "page_obj": page_obj,
            "employees": page_obj.object_list,
            "assignable_roles": assignable_roles,
            "all_roles": all_roles,
            "mentor_candidates": mentor_candidates,
            "manageable_ids": manageable_ids,
            "role_manageable_ids": role_manageable_ids,
            "preservation": preservation,
            "filter_q": p["q"],
            "filter_role_id": p["role_id"],
            "filter_created_from": p["created_from"],
            "filter_created_to": p["created_to"],
            "filter_sort": p["sort"],
            "querystring_no_page": querystring_no_page,
        },
    )


@hr_required
@require_http_methods(["GET", "POST"])
def hr_add_employee(request):
    """Create a new Mentor or Student account with a random password (shown in HR panel)."""
    if request.method == "POST":
        form = HrAddEmployeeForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            role = data["role"]
            mentor = data["mentor"] if role.name.strip().lower() == "student" else None
            plain = _generate_hr_temporary_password()
            user = CustomUserModel.objects.create_user(
                email=data["email"],
                password=plain,
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=role,
                mentor=mentor,
                status=CustomUserModel.UserStatus.ACTIVE,
                password_is_user_chosen=False,
                hr_temporary_password_plain=plain,
            )
            user.is_active = True
            user.save(update_fields=["is_active"])
            messages.success(
                request,
                f"Dodano pracownika: {user.email}. Hasło tymczasowe: {plain} "
                "(widoczne także na liście do czasu pierwszej zmiany hasła przez pracownika).",
            )
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
        return _redirect_hr_dashboard(request)
    _clear_mentor_links(target)
    target.mentor = None
    target.status = CustomUserModel.UserStatus.INACTIVE
    target.is_active = False
    target.hr_temporary_password_plain = ""
    target.save(update_fields=["mentor", "status", "is_active", "hr_temporary_password_plain"])
    messages.success(request, f"Pracownik {target.email} został zwolniony (konto wyłączone).")
    return _redirect_hr_dashboard(request)


@hr_required
@require_http_methods(["POST"])
def hr_reactivate_employee(request, user_id):
    """Re-enable a previously deactivated account."""
    target = get_object_or_404(CustomUserModel, pk=user_id)
    if not _hr_can_manage_actor(request.user, target):
        messages.error(request, "Nie możesz ponownie aktywować tego użytkownika.")
        return _redirect_hr_dashboard(request)
    target.status = CustomUserModel.UserStatus.ACTIVE
    target.is_active = True
    target.save(update_fields=["status", "is_active"])
    messages.success(request, f"Konto {target.email} zostało ponownie włączone.")
    return _redirect_hr_dashboard(request)


@hr_required
@require_http_methods(["POST"])
def hr_change_role(request, user_id):
    """Set role to Mentor or Student only; demoting a mentor clears mentees."""
    target = get_object_or_404(CustomUserModel, pk=user_id)
    if not _hr_can_change_role_for_target(request.user, target):
        messages.error(request, "Nie możesz zmienić roli tego użytkownika.")
        return _redirect_hr_dashboard(request)
    form = HrChangeRoleForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Nieprawidłowe dane formularza roli.")
        return _redirect_hr_dashboard(request)
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
    return _redirect_hr_dashboard(request)


@hr_required
@require_http_methods(["POST"])
def hr_change_email(request, user_id):
    """Update employee email (USERNAME_FIELD); same access rules as role change."""
    target = get_object_or_404(CustomUserModel, pk=user_id)
    if not _hr_can_manage_actor(request.user, target):
        messages.error(request, "Nie możesz zmienić adresu e-mail tego użytkownika.")
        return _redirect_hr_dashboard(request)
    form = HrChangeEmailForm(request.POST, edited_user_pk=target.pk)
    if not form.is_valid():
        err_msg = "Nieprawidłowy adres e-mail lub adres jest już zajęty."
        if form.errors.get("email"):
            err_msg = form.errors["email"][0]
        messages.error(request, err_msg)
        return _redirect_hr_dashboard(request)
    old_email = target.email
    target.email = form.cleaned_data["email"]
    target.save(update_fields=["email"])
    messages.success(
        request,
        f"Zmieniono adres e-mail z „{old_email}” na „{target.email}”.",
    )
    return _redirect_hr_dashboard(request)


@hr_required
@require_http_methods(["POST"])
def hr_change_mentor(request, user_id):
    """Update student's assigned mentor from HR panel."""
    target = get_object_or_404(CustomUserModel, pk=user_id)
    if not _hr_can_manage_actor(request.user, target):
        messages.error(request, "Nie możesz zmienić mentora tego użytkownika.")
        return _redirect_hr_dashboard(request)

    form = HrChangeMentorForm(request.POST, edited_user=target)
    if not form.is_valid():
        err_msg = "Nieprawidłowe dane formularza mentora."
        non_field = form.non_field_errors()
        if non_field:
            err_msg = non_field[0]
        elif form.errors.get("mentor"):
            err_msg = form.errors["mentor"][0]
        messages.error(request, err_msg)
        return _redirect_hr_dashboard(request)

    mentor = form.cleaned_data["mentor"]
    target.mentor = mentor
    target.save(update_fields=["mentor"])
    if mentor:
        messages.success(request, f"Przypisano mentora dla {target.email}: {mentor.email}.")
    else:
        messages.success(request, f"Usunięto przypisanego mentora dla {target.email}.")
    return _redirect_hr_dashboard(request)


@hr_required
@require_http_methods(["POST"])
def hr_reset_user_password(request, user_id):
    """Issue a new temporary password; user must set their own on next login."""
    target = get_object_or_404(CustomUserModel, pk=user_id)
    if not _hr_can_manage_actor(request.user, target):
        messages.error(request, "Nie możesz zresetować hasła temu użytkownikowi.")
        return _redirect_hr_dashboard(request)
    plain = _generate_hr_temporary_password()
    target.set_password(plain)
    target.hr_temporary_password_plain = plain
    target.password_is_user_chosen = False
    target.save(
        update_fields=["password", "hr_temporary_password_plain", "password_is_user_chosen"]
    )
    messages.success(
        request,
        f"Nowe hasło tymczasowe dla {target.email}: {plain}",
    )
    return _redirect_hr_dashboard(request)


@hr_required
@require_http_methods(["GET", "POST"])
def hr_change_own_password(request):
    """HR panel user changes their own password (current password required); no temporary password flow."""
    user = request.user
    if request.method == "POST":
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            user.hr_temporary_password_plain = ""
            user.password_is_user_chosen = True
            user.save(update_fields=["hr_temporary_password_plain", "password_is_user_chosen"])
            update_session_auth_hash(request, user)
            messages.success(request, "Twoje hasło zostało zmienione.")
            return redirect("accounts:hr_dashboard")
    else:
        form = PasswordChangeForm(user)
    apply_bootstrap_control_widgets(form)
    return render(
        request,
        "accounts/hr_change_own_password.html",
        {"form": form},
    )
