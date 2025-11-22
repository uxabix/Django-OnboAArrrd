import random
from datetime import date, timedelta
from onboarding.models import User_tasks, Tasks
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

def run(count=1, group=None):
    users = list(CustomUser.objects.all())
    tasks = list(Tasks.objects.all())

    if not users or not tasks:
        print("Users or tasks missing. Please seed users and tasks first.")
        return

    task_assignments = 0

    for user in users:
        for _ in range(count):
            task = random.choice(tasks)

            assigned_by_candidates = [u for u in users if u != user]
            assigned_by = random.choice(assigned_by_candidates) if assigned_by_candidates else user

            deadline = date.today() + timedelta(days=random.randint(3, 30))

            User_tasks.objects.get_or_create(
                user_id=user,
                task_id=task,
                assigned_by=assigned_by,
                deadline=deadline
            )
            task_assignments += 1

    print(f"Created {task_assignments} user tasks.")
