"""Database models for authentication, roles, and extended user profiles.

This app defines the custom user model used as ``AUTH_USER_MODEL`` plus a
``Roles`` lookup table for application-level authorization (mentor, student,
HR, and so on).
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class Roles(models.Model):
    """Named role assigned to users (mentor, student, HR, etc.)."""

    role_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=60)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"


class CustomUserManager(BaseUserManager):
    """Creates ``CustomUser`` rows with normalized email and optional password."""

    def create_user(self, email, password=None, **extra_fields):
        """Persist a standard (non-staff) user.

        Args:
            email: Login identifier; must be present and is normalized.
            password: Optional; when omitted an unusable password is stored.
            **extra_fields: Additional model fields passed through to the model
                constructor.

        Returns:
            CustomUser: The saved user instance.

        Raises:
            ValueError: If ``email`` is empty after stripping.
        """
        if not email:
            raise ValueError("Email musi być podany")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create an active staff superuser account.

        Args:
            email: Login identifier.
            password: Required non-empty password for interactive superusers.
            **extra_fields: Passed to ``create_user``; ``is_staff`` and
                ``is_superuser`` default to ``True``.

        Returns:
            CustomUser: The saved superuser.

        Raises:
            ValueError: If ``password`` is ``None`` or empty.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("status", CustomUser.UserStatus.ACTIVE)

        if password is None:
            raise ValueError("Superuser musi mieć hasło")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Email-based user with mentor linkage, HR password lifecycle, and gamified stars.

    ``USERNAME_FIELD`` is ``email``. Optional ``mentor`` links students to a
    mentor. HR-created accounts may carry a temporary plaintext password until
    the user chooses their own (see middleware and HR views).
    """

    class UserStatus(models.TextChoices):
        """Lifecycle flag for HR-managed activation."""

        ACTIVE = "active"
        INACTIVE = "inactive"

    mentor = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mentees"
    )

    role = models.ForeignKey(
        Roles,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.INACTIVE,
    )

    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    email = models.EmailField(unique=True)

    created_at = models.DateTimeField(default=timezone.now)

    # wymagane przez Django
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Password lifecycle: HR-generated one-time password shown until user sets their own (see HR panel + middleware).
    password_is_user_chosen = models.BooleanField(default=True)
    hr_temporary_password_plain = models.CharField(max_length=128, blank=True, default="")

    stars = models.IntegerField(default=0, help_text="Liczba gwiazdek za ukończone zadania podopiecznych")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def get_stars_display(self):
        """Return a simple star emoji string for templates.

        Returns:
            str: Repeated star character scaled by ``self.stars``.
        """
        return '⭐' * self.stars

    @property
    def is_mentor(self):
        """Whether this user currently has at least one mentee.

        Returns:
            bool: ``True`` when the reverse ``mentees`` relation is non-empty.
        """
        return self.mentees.exists()
