import random
from onboarding.models import Task_status, User_tasks

def run(count=1, group=None):
    user_tasks = list(User_tasks.objects.all())
    if not user_tasks:
        print("No user tasks found. Please seed user_tasks first.")
        return

    status_choices = [Task_status.Status.DO_ZROBIENIA,
                      Task_status.Status.W_TRAKCIE,
                      Task_status.Status.DO_WERYFIKACJI,
                      Task_status.Status.UKONCZONE]

    total_statuses = 0

    for user_task in user_tasks:
        # Создаём несколько статусов для каждой user_task
        for _ in range(count):
            old_status = random.choice(status_choices)
            new_status = random.choice(status_choices)
            Task_status.objects.get_or_create(
                user_task=user_task,
                old_status=old_status,
                new_status=new_status
            )
            total_statuses += 1

    print(f"Created {total_statuses} task statuses.")
