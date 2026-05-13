"""Human-resources dashboard views for user administration.

Provides paginated employee lists, import/export, activation, mentor assignment,
role changes, and secure temporary password issuance integrated with
``CustomUser`` password lifecycle fields.
"""

import secrets
from io import StringIO
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.apps import apps
from django.core import serializers
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
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
    HrDbExportForm,
    HrDbImportForm,
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
_DB_SERIALIZER_EXTENSIONS = {
    "json": "json",
    "xml": "xml",
    "yaml": "yaml",
}


def _generate_hr_temporary_password():
    """Create a URL-safe random string for HR handoff.

    Returns:
        str: Cryptographically strong token stored as plaintext per product rules.
    """
    return secrets.token_urlsafe(16)


def _clear_mentor_links(user):
    """Remove ``mentor`` references pointing at the given user.

    Args:
        user: ``CustomUser`` being demoted or deactivated.
    """
    CustomUserModel.objects.filter(mentor=user).update(mentor=None)


def _role_name_lower(role):
    """Normalize role name for comparisons.

    Args:
        role: ``Roles`` instance or ``None``.

    Returns:
        str: Lowercased stripped name, or empty string when missing.
    """
    if not role or not role.name:
        return ""
    return role.name.strip().lower()


def _hr_can_manage_actor(actor, target):
    """Return whether ``actor`` may terminate, reactivate, or reset ``target``.

    Rules:
        * Nobody may target themselves.
        * Non-superusers cannot touch superusers.
        * Superusers and Administrator-role users may manage most accounts.
        * Plain HR cannot manage other HR or admin-class roles.

    Args:
        actor: Acting ``CustomUser`` (typically ``request.user``).
        target: Subject ``CustomUser``.

    Returns:
        bool: ``True`` when the action is permitted.
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
    """Whether ``actor`` may change ``target``'s ``Roles`` assignment.

    Superusers and administrators may also edit their own role from the panel.

    Args:
        actor: Acting user.
        target: Subject user.

    Returns:
        bool: ``True`` when role changes are allowed.
    """
    if actor.pk == target.pk:
        return actor.is_superuser or user_is_administrator_role(actor)
    return _hr_can_manage_actor(actor, target)


def _redirect_hr_dashboard(request):
    """Redirect back to the HR list preserving filter query parameters.

    Args:
        request: ``HttpRequest`` whose ``POST`` may include hidden fields
            mirroring the current list state.

    Returns:
        HttpResponseRedirect: Dashboard URL with encoded query string.
    """
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
    """Parse and sanitize GET parameters used by the employee table.

    Args:
        request_get: ``request.GET``-like mapping.

    Returns:
        dict: Keys ``q``, ``filter_role``, ``role_id``, ``created_from``,
        ``created_to``, ``sort``, ``page`` with validated defaults.
    """
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
    """Apply text, role, and creation-date filters to a user queryset.

    Args:
        qs: Base ``QuerySet`` of users.
        p: Dict produced by ``_parse_hr_list_params``.

    Returns:
        QuerySet: Filtered queryset.
    """
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
    """Build hidden-field values so POST actions keep list pagination and filters.

    Args:
        p: Parsed list parameter dict.
        page_number: Current 1-based page index.

    Returns:
        dict: Field names and string values for templates.
    """
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
    """Serialize current filters without the ``page`` key for pager links.

    Args:
        request_get: ``request.GET``-like mapping.

    Returns:
        str: URL-encoded query string.
    """
    mutable = request_get.copy()
    if "page" in mutable:
        del mutable["page"]
    return mutable.urlencode()


@hr_required
def hr_dashboard(request):
    """Render the paginated HR employee list with inline management actions.

    Args:
        request: Authenticated HR-eligible ``HttpRequest``.

    Returns:
        HttpResponse: ``accounts/hr_dashboard.html`` with forms and metadata.
    """
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
    mentor_ids_on_page = [
        u.pk for u in page_obj.object_list
        if u.role and (u.role.name or "").strip().lower() == "mentor"
    ]
    mentees_by_mentor_id = {}
    if mentor_ids_on_page:
        mentees_qs = (
            CustomUserModel.objects.filter(mentor_id__in=mentor_ids_on_page)
            .select_related("role", "mentor")
            .order_by("mentor_id", "first_name", "last_name", "email")
        )
        for mentee in mentees_qs:
            mentees_by_mentor_id.setdefault(mentee.mentor_id, []).append(mentee)

    employees = list(page_obj.object_list)
    for employee in employees:
        if employee.role and (employee.role.name or "").strip().lower() == "mentor":
            employee.hr_mentees = mentees_by_mentor_id.get(employee.pk, [])
            employee.hr_mentees_count = len(employee.hr_mentees)
        else:
            employee.hr_mentees = []
            employee.hr_mentees_count = 0
    querystring_no_page = _querystring_except_page(request.GET)
    db_export_form = HrDbExportForm()
    db_import_form = HrDbImportForm()

    return render(
        request,
        "accounts/hr_dashboard.html",
        {
            "page_obj": page_obj,
            "employees": employees,
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
            "db_export_form": db_export_form,
            "db_import_form": db_import_form,
        },
    )


@hr_required
@require_http_methods(["POST"])
def hr_export_database(request):
    """Stream a database export using Django's serialization framework.

    Returns:
        HttpResponse: File download on success or redirect with flash message.
    """
    form = HrDbExportForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Nieprawidłowy format eksportu.")
        return redirect("accounts:hr_dashboard")

    export_format = form.cleaned_data["export_format"]
    data_scope = form.cleaned_data["data_scope"]
    only_selected = form.cleaned_data["only_selected"]
    user_ids = form.cleaned_data.get("selected_user_ids_list", [])
    task_ids = form.cleaned_data.get("selected_task_ids_list", [])

    try:
        if data_scope == "full_db":
            stream = StringIO()
            call_command("dumpdata", format=export_format, indent=2, stdout=stream)
            payload = stream.getvalue()
        elif data_scope == "users_only":
            payload = _export_users_only(export_format, only_selected, user_ids)
        else:
            payload = _export_users_mentors_tasks(export_format, only_selected, user_ids, task_ids)
    except (CommandError, ValueError) as exc:
        messages.error(request, f"Eksport nie powiódł się: {exc}")
        return redirect("accounts:hr_dashboard")

    filename = form.build_filename()
    extension = _DB_SERIALIZER_EXTENSIONS[export_format]
    content_type = "application/json" if extension == "json" else "application/octet-stream"
    response = HttpResponse(payload, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@hr_required
@require_http_methods(["POST"])
def hr_import_database(request):
    """Import serialized fixtures with optional overwrite semantics.

    Returns:
        HttpResponse: Redirect with success or error flash message.
    """
    form = HrDbImportForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "Nieprawidłowy plik importu.")
        return redirect("accounts:hr_dashboard")

    uploaded = form.cleaned_data["data_file"]
    overwrite_existing = form.cleaned_data["overwrite_existing"]
    filename = uploaded.name
    suffix = ""
    if "." in filename:
        suffix = "." + filename.rsplit(".", 1)[1].lower()

    try:
        file_bytes = b"".join(uploaded.chunks())
        payload = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        messages.error(request, "Plik importu musi być w kodowaniu UTF-8.")
        return redirect("accounts:hr_dashboard")

    fmt = "yaml" if suffix in (".yaml", ".yml") else suffix.lstrip(".")
    if fmt not in ("json", "xml", "yaml"):
        messages.error(request, "Nieobsługiwany format pliku importu.")
        return redirect("accounts:hr_dashboard")

    try:
        created, updated, skipped = _import_payload(payload, fmt, overwrite_existing)
    except Exception as exc:  # noqa: BLE001
        messages.error(request, f"Import nie powiódł się: {exc}")
        return redirect("accounts:hr_dashboard")

    mode_msg = "nadpisano istniejące rekordy" if overwrite_existing else "istniejące rekordy pominięto"
    messages.success(
        request,
        f"Import zakończony: dodano {created}, zaktualizowano {updated}, pominięto {skipped} ({mode_msg}).",
    )
    return redirect("accounts:hr_dashboard")


def _serialize_objects(export_format, objects):
    """Serialize model instances to the requested dump format.

    Args:
        export_format: ``json``, ``xml``, or ``yaml`` accepted by Django.
        objects: Iterable of model instances.

    Returns:
        str: Serialized payload text.
    """
    return serializers.serialize(export_format, objects, indent=2)


def _export_users_only(export_format, only_selected, user_ids):
    """Export roles plus users (and mentors of selected users when filtered).

    Args:
        export_format: Serializer format name.
        only_selected: When ``True``, restrict to ``user_ids``.
        user_ids: Primary keys referenced by the export form.

    Returns:
        str: Serialized text blob.
    """
    users_qs = CustomUserModel.objects.select_related("role", "mentor").all()
    if only_selected:
        users_qs = users_qs.filter(pk__in=user_ids)
        mentor_ids = set(users_qs.exclude(mentor_id__isnull=True).values_list("mentor_id", flat=True))
        if mentor_ids:
            users_qs = CustomUserModel.objects.filter(Q(pk__in=user_ids) | Q(pk__in=mentor_ids))
    role_ids = set(users_qs.exclude(role_id__isnull=True).values_list("role_id", flat=True))
    roles_qs = Roles.objects.filter(pk__in=role_ids) if role_ids else Roles.objects.none()
    objects = list(roles_qs.order_by("pk")) + list(users_qs.order_by("pk"))
    return _serialize_objects(export_format, objects)


def _export_users_mentors_tasks(export_format, only_selected, user_ids, task_ids):
    """Export a graph of users, competency paths, tasks, and status history.

    Args:
        export_format: Serializer format name.
        only_selected: Whether to restrict to provided id lists.
        user_ids: User primary keys for selective export.
        task_ids: Task primary keys for selective export.

    Returns:
        str: Serialized text blob covering related models.
    """
    TasksModel = _get_model("onboarding.Tasks")
    UserTasksModel = _get_model("onboarding.User_tasks")
    TaskStatusModel = _get_model("onboarding.Task_status")
    TaskTypesModel = _get_model("onboarding.Task_types")
    PathsModel = _get_model("onboarding.Competency_paths")

    if only_selected:
        tasks_qs = TasksModel.objects.filter(pk__in=task_ids) if task_ids else TasksModel.objects.none()
        user_tasks_qs = UserTasksModel.objects.filter(
            Q(user_id_id__in=user_ids) | Q(assigned_by_id__in=user_ids) | Q(task_id_id__in=task_ids)
        )
        if task_ids:
            user_tasks_qs = user_tasks_qs | UserTasksModel.objects.filter(task_id_id__in=task_ids)
        user_tasks_qs = user_tasks_qs.distinct()
        related_user_ids = set(user_ids)
        related_user_ids.update(user_tasks_qs.exclude(user_id_id__isnull=True).values_list("user_id_id", flat=True))
        related_user_ids.update(user_tasks_qs.exclude(assigned_by_id__isnull=True).values_list("assigned_by_id", flat=True))
        related_user_ids.update(CustomUserModel.objects.filter(pk__in=related_user_ids).exclude(mentor_id__isnull=True).values_list("mentor_id", flat=True))
        users_qs = CustomUserModel.objects.filter(pk__in=related_user_ids)
    else:
        tasks_qs = TasksModel.objects.all()
        user_tasks_qs = UserTasksModel.objects.all()
        users_qs = CustomUserModel.objects.all()

    statuses_qs = TaskStatusModel.objects.filter(user_task_id__in=user_tasks_qs.values("pk"))
    task_type_ids = set(tasks_qs.exclude(task_type_id__isnull=True).values_list("task_type_id", flat=True))
    path_ids = set(tasks_qs.exclude(path_id__isnull=True).values_list("path_id", flat=True))
    task_types_qs = TaskTypesModel.objects.filter(pk__in=task_type_ids)
    paths_qs = PathsModel.objects.filter(pk__in=path_ids)
    role_ids = set(users_qs.exclude(role_id__isnull=True).values_list("role_id", flat=True))
    roles_qs = Roles.objects.filter(pk__in=role_ids)

    objects = (
        list(roles_qs.order_by("pk"))
        + list(users_qs.order_by("pk"))
        + list(paths_qs.order_by("pk"))
        + list(task_types_qs.order_by("pk"))
        + list(tasks_qs.order_by("pk"))
        + list(user_tasks_qs.order_by("pk"))
        + list(statuses_qs.order_by("pk"))
    )
    return _serialize_objects(export_format, objects)


def _get_model(model_label):
    """Resolve an ``app_label.ModelName`` string via Django's app registry.

    Args:
        model_label: Dotted model identifier.

    Returns:
        type: Concrete model class.
    """
    app_label, model_name = model_label.split(".")
    return apps.get_model(app_label, model_name)


def _import_payload(payload, fmt, overwrite_existing):
    """Deserialize and persist objects inside a single atomic transaction.

    Args:
        payload: UTF-8 text accepted by ``serializers.deserialize``.
        fmt: Serializer format name.
        overwrite_existing: When ``False``, skip rows whose PK already exists.

    Returns:
        tuple[int, int, int]: Counts ``(created, updated, skipped)``.
    """
    created = 0
    updated = 0
    skipped = 0
    with transaction.atomic():
        for deserialized in serializers.deserialize(fmt, payload):
            instance = deserialized.object
            model = instance.__class__
            instance_pk = instance.pk
            exists = bool(instance_pk) and model.objects.filter(pk=instance_pk).exists()
            if exists and not overwrite_existing:
                skipped += 1
                continue
            deserialized.save()
            if exists:
                updated += 1
            else:
                created += 1
    return created, updated, skipped


@hr_required
@require_http_methods(["GET", "POST"])
def hr_add_employee(request):
    """Create a mentor or student with an HR-issued temporary password.

    Returns:
        HttpResponse: Form on ``GET`` or redirect to dashboard after success.
    """
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
    """Deactivate a user, clear mentee links, and drop stored HR passwords.

    Args:
        request: Authenticated HR request with POSTed preservation fields.
        user_id: Primary key of the employee to terminate.

    Returns:
        HttpResponse: Redirect to the filtered dashboard list.
    """
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
    """Re-enable a previously deactivated employee account.

    Args:
        request: Authenticated HR request.
        user_id: Target user's primary key.

    Returns:
        HttpResponse: Redirect back to the dashboard list.
    """
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
    """Assign a new mentor/student role, clearing mentees when demoting mentors.

    Args:
        request: POST with ``HrChangeRoleForm`` fields plus hidden list state.
        user_id: Target user's primary key.

    Returns:
        HttpResponse: Redirect to the dashboard preserving filters.
    """
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
    """Update a user's login email with uniqueness validation.

    Args:
        request: POSTed ``HrChangeEmailForm`` data.
        user_id: Target user's primary key.

    Returns:
        HttpResponse: Redirect with flash messaging.
    """
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
    """Assign or clear a student's mentor from the HR panel.

    Args:
        request: POST body with ``HrChangeMentorForm`` fields.
        user_id: Student primary key.

    Returns:
        HttpResponse: Redirect with validation or success messaging.
    """
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
    """Issue a new temporary password and force change on next login.

    Args:
        request: Authenticated HR request.
        user_id: Target user's primary key.

    Returns:
        HttpResponse: Redirect with plaintext password echoed once.
    """
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
    """Allow HR staff to rotate their own password without the temporary-password flow.

    Returns:
        HttpResponse: ``PasswordChangeForm`` template or redirect on success.
    """
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
