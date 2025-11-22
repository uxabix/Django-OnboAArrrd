import random
from django.utils import timezone
from faker import Faker
from accounts.models import CustomUser, Roles
from django.contrib.auth.models import Group

fake = Faker()

def run(count=10, group: Group = None):
    roles = list(Roles.objects.all())
    if not roles:
        print("No roles found. Please seed roles first.")
        return

    users = []

    # Создаем пользователей
    for _ in range(count):
        role = random.choice(roles)
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = fake.unique.email()

        user = CustomUser.objects.create_user(
            email=email,
            password="Test1234!",
            first_name=first_name,
            last_name=last_name,
            role_id=role
        )
        users.append(user)

        if group:
            user.groups.add(group)

    # Назначаем случайных менторов (только для пользователей не-Admin)
    mentors = [u for u in users if u.role_id.name.lower() == "mentor"]
    students = [u for u in users if u.role_id.name.lower() == "student"]

    for student in students:
        if mentors:
            student.mentor_id = random.choice(mentors)
            student.save()

    print(f"Created {len(users)} users.")
