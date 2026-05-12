from accounts.models import CustomUser, Roles
from django.contrib.auth.models import Group


DEMO_USERS = [
    {"email": "admin.demo@onboard.local", "password": "DemoAdmin123!", "first_name": "Alicja", "last_name": "Admin", "role": "Admin"},
    {"email": "hr.demo@onboard.local", "password": "DemoHr123!", "first_name": "Hanna", "last_name": "HR", "role": "HR"},
    {"email": "mentor.piotr@onboard.local", "password": "DemoMentor123!", "first_name": "Piotr", "last_name": "Nowak", "role": "Mentor"},
    {"email": "mentor.marta@onboard.local", "password": "DemoMentor123!", "first_name": "Marta", "last_name": "Kowalska", "role": "Mentor"},
    {"email": "mentor.tomasz@onboard.local", "password": "DemoMentor123!", "first_name": "Tomasz", "last_name": "Lis", "role": "Mentor"},
    {"email": "student.ola@onboard.local", "password": "DemoStudent123!", "first_name": "Ola", "last_name": "Mazur", "role": "Student"},
    {"email": "student.kamil@onboard.local", "password": "DemoStudent123!", "first_name": "Kamil", "last_name": "Krupa", "role": "Student"},
    {"email": "student.julia@onboard.local", "password": "DemoStudent123!", "first_name": "Julia", "last_name": "Wojcik", "role": "Student"},
    {"email": "student.adam@onboard.local", "password": "DemoStudent123!", "first_name": "Adam", "last_name": "Zielinski", "role": "Student"},
    {"email": "student.nina@onboard.local", "password": "DemoStudent123!", "first_name": "Nina", "last_name": "Czajka", "role": "Student"},
]


def _role_map():
    return {role.name.strip().lower(): role for role in Roles.objects.all()}


def run(count=10, group: Group = None):
    roles = _role_map()
    if not roles:
        print("No roles found. Please seed roles first.")
        return

    created_or_updated = []
    for entry in DEMO_USERS:
        role = roles.get(entry["role"].lower())
        if role is None:
            continue

        user, created = CustomUser.objects.get_or_create(
            email=entry["email"],
            defaults={
                "first_name": entry["first_name"],
                "last_name": entry["last_name"],
                "role": role,
                "status": CustomUser.UserStatus.ACTIVE,
                "is_active": True,
            },
        )
        if created:
            user.set_password(entry["password"])
            user.save(update_fields=["password"])
        else:
            user.first_name = entry["first_name"]
            user.last_name = entry["last_name"]
            user.role = role
            user.status = CustomUser.UserStatus.ACTIVE
            user.is_active = True
            user.set_password(entry["password"])
            user.save(update_fields=["first_name", "last_name", "role", "status", "is_active", "password"])

        if group:
            user.groups.add(group)
        created_or_updated.append((user, entry["password"], entry["role"]))

    CustomUser.objects.filter(role__name__iexact="Mentor").update(stars=0)
    CustomUser.objects.filter(is_superuser=True).update(stars=0)

    mentors = list(CustomUser.objects.filter(role__name__iexact="Mentor").order_by("id"))
    students = list(CustomUser.objects.filter(role__name__iexact="Student").order_by("id"))
    superusers = list(CustomUser.objects.filter(is_superuser=True).order_by("id"))

    mentor_pool = mentors + superusers
    for idx, student in enumerate(students):
        assigned_mentor = mentor_pool[idx % len(mentor_pool)] if mentor_pool else None
        student.mentor = assigned_mentor
        student.save(update_fields=["mentor"])

    if superusers and students:
        superuser_ids = {su.id for su in superusers}
        linked_to_superusers = [s for s in students if s.mentor_id in superuser_ids]
        if not linked_to_superusers:
            students[0].mentor = superusers[0]
            students[0].save(update_fields=["mentor"])

    print(f"Prepared {len(created_or_updated)} demo users.")
    print("\n" + "=" * 90)
    print("Demo login accounts")
    print("=" * 90)
    for user, password, role in created_or_updated:
        full_name = f"{user.first_name} {user.last_name}".strip()
        mentor_email = user.mentor.email if user.mentor else "-"
        print(f"{role:<8} | {user.email:<32} | {password:<18} | {full_name:<22} | mentor: {mentor_email}")
    print("=" * 90 + "\n")
