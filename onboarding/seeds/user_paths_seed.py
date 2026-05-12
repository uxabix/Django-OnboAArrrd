from onboarding.models import User_paths, Competency_paths
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

def run(count=1, group=None):
    users = list(CustomUser.objects.filter(role__name__iexact="Student"))
    paths = list(Competency_paths.objects.all())
    assigners = list(CustomUser.objects.filter(role__name__in=["Mentor", "HR", "Admin"]))
    if not assigners:
        assigners = list(CustomUser.objects.filter(is_superuser=True))

    if not users or not paths:
        print("Users or paths missing. Please seed users and competency paths first.")
        return

    assignments = 0
    for idx, user in enumerate(users):
        primary_path = paths[idx % len(paths)]
        secondary_path = paths[(idx + 1) % len(paths)] if len(paths) > 1 and idx % 2 == 0 else None
        assigned_by = user.mentor or (assigners[idx % len(assigners)] if assigners else user)

        for path in [primary_path, secondary_path]:
            if path is None:
                continue
            _, created = User_paths.objects.get_or_create(
                user=user,
                path=path,
                defaults={"assigned_by": assigned_by},
            )
            if not created and assigned_by and not User_paths.objects.filter(user=user, path=path, assigned_by=assigned_by).exists():
                User_paths.objects.filter(user=user, path=path).update(assigned_by=assigned_by)
            assignments += 1

    print(f"Assigned {assignments} paths to users.")
