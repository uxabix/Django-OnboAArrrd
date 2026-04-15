import random
from accounts.models import CustomUser, Roles
from django.contrib.auth.models import Group

def run(count=10, group: Group = None):
    roles = list(Roles.objects.all())
    if not roles:
        print("No roles found. Please seed roles first.")
        return

    mentor_role = next((r for r in roles if r.name.lower() == "mentor"), None)
    student_role = next((r for r in roles if r.name.lower() == "student"), None)
    hr_role = next((r for r in roles if r.name.lower() == "hr"), None)

    users = []
    test_accounts = []

    # Test HR account (panel kadrowy)
    if hr_role:
        hr_user = CustomUser.objects.create_user(
            email="hr@test.com",
            password="hr12345",
            first_name="Anna",
            last_name="Kadry",
            role=hr_role,
            status=CustomUser.UserStatus.ACTIVE,
        )
        hr_user.is_active = True
        hr_user.save(update_fields=["is_active"])
        users.append(hr_user)
        test_accounts.append({
            "email": "hr@test.com",
            "password": "hr12345",
            "role": "HR",
            "name": "Anna Kadry",
        })
        if group:
            hr_user.groups.add(group)

    # Create test mentors with simple password
    test_mentors_data = [
        {"first_name": "John", "last_name": "Mentor", "email": "mentor1@test.com"},
        {"first_name": "Sarah", "last_name": "Guide", "email": "mentor2@test.com"},
        {"first_name": "Mike", "last_name": "Coach", "email": "mentor3@test.com"},
    ]

    for mentor_data in test_mentors_data:
        user = CustomUser.objects.create_user(
            email=mentor_data["email"],
            password="mentor",
            first_name=mentor_data["first_name"],
            last_name=mentor_data["last_name"],
            role=mentor_role,
            status=CustomUser.UserStatus.ACTIVE
        )
        users.append(user)
        test_accounts.append({
            "email": mentor_data["email"],
            "password": "mentor",
            "role": "Mentor",
            "name": f"{mentor_data['first_name']} {mentor_data['last_name']}"
        })
        if group:
            user.groups.add(group)

    # Create test students with simple password
    test_students_data = [
        {"first_name": "Alex", "last_name": "Student", "email": "student1@test.com"},
        {"first_name": "Emma", "last_name": "Learner", "email": "student2@test.com"},
        {"first_name": "David", "last_name": "Novice", "email": "student3@test.com"},
    ]

    for student_data in test_students_data:
        user = CustomUser.objects.create_user(
            email=student_data["email"],
            password="student",
            first_name=student_data["first_name"],
            last_name=student_data["last_name"],
            role=student_role,
            status=CustomUser.UserStatus.ACTIVE
        )
        users.append(user)
        test_accounts.append({
            "email": student_data["email"],
            "password": "student",
            "role": "Student",
            "name": f"{student_data['first_name']} {student_data['last_name']}"
        })
        if group:
            user.groups.add(group)

    # Create random users
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
            role=role,
            status=CustomUser.UserStatus.ACTIVE
        )
        users.append(user)

        if group:
            user.groups.add(group)

    # Assign mentors to students
    mentors = [u for u in users if u.role and u.role.name.lower() == "mentor"]
    students = [u for u in users if u.role and u.role.name.lower() == "student"]

    for student in students:
        if mentors:
            student.mentor = random.choice(mentors)
            student.save()

    print(f"Created {len(users)} users.")

    # Test accounts data
    print("\n" + "="*70)
    print("Test accounts:")
    print("="*70)
    print("\nMENTORS:")
    for acc in test_accounts:
        if acc["role"] == "Mentor":
            print(f"  Email: {acc['email']:<25} Password: {acc['password']:<15} ({acc['name']})")

    print("\nSTUDENTS:")
    for acc in test_accounts:
        if acc["role"] == "Student":
            print(f"  Email: {acc['email']:<25} Password: {acc['password']:<15} ({acc['name']})")

    print("\nHR:")
    for acc in test_accounts:
        if acc["role"] == "HR":
            print(f"  Email: {acc['email']:<25} Password: {acc['password']:<15} ({acc['name']})")
    print("="*70 + "\n")

    return test_accounts
