# accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Tworzy i zapisuje użytkownika o podanym emailu i haśle.
        """
        if not email:
            raise ValueError("Email musi być podany")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)  # ustawia hashed password w user.password
        else:
            user.set_unusable_password()
        # opcjonalnie synchronizuj password_hash z zaszyfrowanym hasłem (nie surowym)
        user.password_hash = user.password or ''
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("status", "active")

        if password is None:
            raise ValueError("Superuser musi mieć hasło")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    # Możesz usunąć password_hash jeśli nie potrzebujesz redundancji. Jeśli zostaje, przechowuj hash (nie surowe).
    password_hash = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, default="inactive")

    # wymagane przez Django
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        # jeśli password jest już hashed w self.password (np. po set_password),
        # synchronizuj password_hash z tą wartością (ale nie zapisuj surowego hasła)
        if self.password:
            self.password_hash = self.password
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
