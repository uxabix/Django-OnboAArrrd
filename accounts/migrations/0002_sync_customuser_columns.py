"""Synchronizacja kolumn modelu CustomUser z bazą danych.

Historia migracji `accounts` została zregenerowana — `0001_initial` opisuje
dziś końcowy stan modelu, ale w istniejących bazach mogą brakować części
kolumn (np. `stars`, `password_is_user_chosen`, `hr_temporary_password_plain`),
ponieważ stare migracje 0002–0006 zostały usunięte przed ich pełnym wdrożeniem.

Ta migracja używa `SeparateDatabaseAndState`, by dodać brakujące kolumny
wyłącznie po stronie bazy danych (stan modelu w Django jest już aktualny po
0001_initial). `IF NOT EXISTS` pozwala bezpiecznie uruchomić migrację również
na świeżej bazie, gdzie 0001_initial utworzył te kolumny od razu.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                # Pola dziedziczone z AbstractBaseUser
                "ALTER TABLE accounts_customuser "
                "ADD COLUMN IF NOT EXISTS password VARCHAR(128) NOT NULL DEFAULT '';",
                "ALTER TABLE accounts_customuser "
                "ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE NULL;",
                # Pola dodane wraz z funkcjami HR / mentora
                "ALTER TABLE accounts_customuser "
                "ADD COLUMN IF NOT EXISTS password_is_user_chosen BOOLEAN NOT NULL DEFAULT TRUE;",
                "ALTER TABLE accounts_customuser "
                "ADD COLUMN IF NOT EXISTS hr_temporary_password_plain VARCHAR(128) NOT NULL DEFAULT '';",
                "ALTER TABLE accounts_customuser "
                "ADD COLUMN IF NOT EXISTS stars INTEGER NOT NULL DEFAULT 0;",
            ],
            reverse_sql=[
                "ALTER TABLE accounts_customuser DROP COLUMN IF EXISTS stars;",
                "ALTER TABLE accounts_customuser DROP COLUMN IF EXISTS hr_temporary_password_plain;",
                "ALTER TABLE accounts_customuser DROP COLUMN IF EXISTS password_is_user_chosen;",
                # Nie usuwamy `password` i `last_login` — są wymagane przez Django.
            ],
            state_operations=[],
        ),
    ]
