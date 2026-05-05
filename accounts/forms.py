from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from .models import Roles

CustomUser = get_user_model()


def apply_bootstrap_control_widgets(form):
    """Add Bootstrap form-control class to all fields on auth-style forms."""
    for field in form.fields.values():
        field.widget.attrs.setdefault("class", "form-control")


def mentor_student_roles_queryset():
    """Roles that HR may assign: Mentor and Student (seed names, case-insensitive)."""
    return Roles.objects.filter(
        Q(name__iexact="Mentor") | Q(name__iexact="Student")
    ).order_by("name")


class HrAddEmployeeForm(forms.Form):
    """Create a new employee as Mentor or Student (Polish labels in Meta/widgets)."""

    email = forms.EmailField(
        label="Adres e-mail",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    first_name = forms.CharField(
        label="Imię",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        label="Nazwisko",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    role = forms.ModelChoiceField(
        label="Rola",
        queryset=mentor_student_roles_queryset(),
        empty_label=None,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    mentor = forms.ModelChoiceField(
        label="Mentor (opcjonalnie, tylko dla ucznia)",
        queryset=CustomUser.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        mentor_qs = CustomUser.objects.filter(
            role__name__iexact="Mentor"
        ).order_by("first_name", "last_name", "email")
        self.fields["mentor"].queryset = mentor_qs

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Użytkownik z tym adresem e-mail już istnieje.")
        return email

    def clean(self):
        data = super().clean()
        role = data.get("role")
        mentor = data.get("mentor")
        if role and role.name.strip().lower() != "student" and mentor:
            self.add_error("mentor", "Mentora można przypisać tylko uczniowi.")
        return data


class HrChangeRoleForm(forms.Form):
    """Switch employee role between Mentor and Student."""

    role = forms.ModelChoiceField(
        label="Nowa rola",
        queryset=mentor_student_roles_queryset(),
        empty_label=None,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )


class HrChangeEmailForm(forms.Form):
    """Update employee login email from the HR panel (Polish labels)."""

    email = forms.EmailField(
        label="Adres e-mail",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control form-control-sm hr-email-input",
                "autocomplete": "email",
            }
        ),
    )

    def __init__(self, *args, edited_user_pk=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.edited_user_pk = edited_user_pk

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = CustomUser.objects.filter(email__iexact=email)
        if self.edited_user_pk is not None:
            qs = qs.exclude(pk=self.edited_user_pk)
        if qs.exists():
            raise forms.ValidationError("Użytkownik z tym adresem e-mail już istnieje.")
        return email


class HrChangeMentorForm(forms.Form):
    """Update assigned mentor for an existing student account."""

    mentor = forms.ModelChoiceField(
        label="Mentor",
        queryset=CustomUser.objects.none(),
        required=False,
        empty_label="Brak mentora",
        widget=forms.Select(attrs={"class": "form-select form-select-sm hr-role-select"}),
    )

    def __init__(self, *args, edited_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.edited_user = edited_user
        self.fields["mentor"].queryset = CustomUser.objects.filter(
            role__name__iexact="Mentor"
        ).order_by("first_name", "last_name", "email")

    def clean(self):
        data = super().clean()
        mentor = data.get("mentor")
        target = self.edited_user
        if not target:
            return data

        if target.role is None or target.role.name.strip().lower() != "student":
            raise forms.ValidationError("Mentora można przypisać tylko użytkownikowi z rolą Student.")

        if mentor and mentor.pk == target.pk:
            self.add_error("mentor", "Użytkownik nie może być swoim mentorem.")

        return data


class HrDbExportForm(forms.Form):
    """Choose a serializer format for full database export."""

    FORMAT_CHOICES = (
        ("json", "JSON (.json)"),
        ("xml", "XML (.xml)"),
        ("yaml", "YAML (.yaml)"),
    )

    export_format = forms.ChoiceField(
        label="Format eksportu",
        choices=FORMAT_CHOICES,
        initial="json",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    DATA_SCOPE_CHOICES = (
        ("full_db", "Pełna baza danych"),
        ("users_only", "Tylko użytkownicy i role"),
        ("users_mentors_tasks", "Użytkownicy + mentorzy + zadania"),
    )
    data_scope = forms.ChoiceField(
        label="Zakres danych",
        choices=DATA_SCOPE_CHOICES,
        initial="full_db",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    only_selected = forms.BooleanField(
        label="Eksportuj tylko wybrane rekordy (po ID)",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    selected_user_ids = forms.CharField(
        label="ID użytkowników",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "np. 1,2,5"}),
    )
    selected_task_ids = forms.CharField(
        label="ID zadań",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "np. 10,11"}),
    )

    @staticmethod
    def _parse_ids(raw_value):
        if not raw_value:
            return []
        out = []
        for part in raw_value.split(","):
            part = part.strip()
            if not part:
                continue
            if not part.isdigit():
                raise forms.ValidationError("ID muszą być liczbami całkowitymi rozdzielonymi przecinkami.")
            out.append(int(part))
        return sorted(set(out))

    def clean(self):
        cleaned = super().clean()
        cleaned["selected_user_ids_list"] = self._parse_ids(cleaned.get("selected_user_ids", ""))
        cleaned["selected_task_ids_list"] = self._parse_ids(cleaned.get("selected_task_ids", ""))
        if cleaned.get("only_selected"):
            scope = cleaned.get("data_scope")
            has_users = bool(cleaned["selected_user_ids_list"])
            has_tasks = bool(cleaned["selected_task_ids_list"])
            if scope == "users_only" and not has_users:
                self.add_error("selected_user_ids", "Podaj co najmniej jedno ID użytkownika.")
            if scope == "users_mentors_tasks" and not (has_users or has_tasks):
                self.add_error(
                    "selected_user_ids",
                    "Dla tego zakresu podaj ID użytkowników i/lub ID zadań.",
                )
            if scope == "full_db":
                raise forms.ValidationError("Dla pełnej bazy nie używaj filtrowania po ID.")
        return cleaned

    def build_filename(self):
        fmt = self.cleaned_data["export_format"]
        scope = self.cleaned_data.get("data_scope", "full_db")
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        extension = "yaml" if fmt == "yaml" else fmt
        return f"db_export_{scope}_{timestamp}.{extension}"


class HrDbImportForm(forms.Form):
    """Upload fixture-like database dump accepted by loaddata."""

    data_file = forms.FileField(
        label="Plik kopii danych",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".json,.xml,.yaml,.yml"}),
    )
    overwrite_existing = forms.BooleanField(
        label="Nadpisuj istniejące rekordy",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean_data_file(self):
        uploaded = self.cleaned_data["data_file"]
        filename = (uploaded.name or "").lower()
        allowed_suffixes = (".json", ".xml", ".yaml", ".yml")
        if not filename.endswith(allowed_suffixes):
            raise forms.ValidationError("Dozwolone rozszerzenia: .json, .xml, .yaml, .yml.")
        return uploaded
