import random
from onboarding.models import User_paths, Competency_paths
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

def run(count=1, group=None):
    users = list(CustomUser.objects.all())
    paths = list(Competency_paths.objects.all())

    if not users or not paths:
        print("Users or paths missing. Please seed users and competency paths first.")
        return

    assignments = 0
    for user in users:
        for _ in range(count):
            path = random.choice(paths)
            assigned_by = random.choice(users)  # Mentor or student
            User_paths.objects.get_or_create(
                user=user,
                path=path,
                assigned_by=assigned_by
            )
            assignments += 1

    print(f"Assigned {assignments} paths to users.")
