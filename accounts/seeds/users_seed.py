import random
from accounts.models import CustomUser, Roles
from django.contrib.auth.models import Group

def run(count=10, group: Group = None):
    roles = list(Roles.objects.all())
    if not roles:
        print("No roles found. Please seed roles first.")
        return

    users = []

    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Hank", "Ivy", "Jack"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Taylor", "Anderson"]

    for i in range(count):
        role = random.choice(roles)
        first_name = first_names[i % len(first_names)]
        last_name = last_names[i % len(last_names)]
        email = f"{first_name.lower()}.{last_name.lower()}{i}@test.com"

        user = CustomUser.objects.create_user(
            email=email,
            password="Test1234!",
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        users.append(user)

        if group:
            user.groups.add(group)

    # Назначаем менторов студентам
    mentors = [u for u in users if u.role and u.role.name.lower() == "mentor"]
    students = [u for u in users if u.role and u.role.name.lower() == "student"]

    for student in students:
        if mentors:
            student.mentor = random.choice(mentors)
            student.save()

    print(f"Created {len(users)} users.")
