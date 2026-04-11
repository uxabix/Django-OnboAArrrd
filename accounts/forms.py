from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Roles

CustomUser = get_user_model()


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
    password1 = forms.CharField(
        label="Hasło",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Powtórz hasło",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
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
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Hasła muszą być identyczne.")
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
