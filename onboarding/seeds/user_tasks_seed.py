from datetime import date, timedelta
from onboarding.models import User_tasks, Tasks
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

def run(count=1, group=None):
    users = list(CustomUser.objects.filter(role__name__iexact="Student").select_related("mentor"))
    tasks = list(Tasks.objects.all())

    if not users or not tasks:
        print("Users or tasks missing. Please seed users and tasks first.")
        return

    task_assignments = 0
    today = date.today()

    # 5 scenariuszy deadline, aby pokryc demo statusow:
    # on_time, late, overdue, in_progress, todo
    scenario_deadlines = [
        today - timedelta(days=1),
        today - timedelta(days=5),
        today - timedelta(days=3),
        today + timedelta(days=4),
        today + timedelta(days=10),
    ]

    for user_idx, student in enumerate(users):
        for scenario_idx, deadline in enumerate(scenario_deadlines):
            task = tasks[(user_idx + scenario_idx) % len(tasks)]
            assigned_by = student.mentor or student
            _, created = User_tasks.objects.get_or_create(
                user_id=student,
                task_id=task,
                defaults={
                    "assigned_by": assigned_by,
                    "deadline": deadline,
                },
            )
            if not created:
                User_tasks.objects.filter(user_id=student, task_id=task).update(
                    assigned_by=assigned_by,
                    deadline=deadline,
                )
            task_assignments += 1

    print(f"Prepared {task_assignments} user tasks.")
