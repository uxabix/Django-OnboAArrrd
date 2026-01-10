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
        # Make realistic chain of statuses
        # First status: From None to DO_ZROBIENIA
        Task_status.objects.get_or_create(
            user_task=user_task,
            old_status=None,
            new_status=Task_status.Status.DO_ZROBIENIA
        )
        total_statuses += 1

        # Other statuses - task progression
        current_status = Task_status.Status.DO_ZROBIENIA
        for _ in range(count):
            # Choose new status based on current status
            if current_status == Task_status.Status.DO_ZROBIENIA:
                new_status = random.choice([Task_status.Status.W_TRAKCIE, Task_status.Status.DO_ZROBIENIA])
            elif current_status == Task_status.Status.W_TRAKCIE:
                new_status = random.choice([Task_status.Status.DO_WERYFIKACJI, Task_status.Status.W_TRAKCIE])
            elif current_status == Task_status.Status.DO_WERYFIKACJI:
                new_status = random.choice([Task_status.Status.UKONCZONE, Task_status.Status.W_TRAKCIE])
            else:
                new_status = Task_status.Status.UKONCZONE

            if new_status != current_status:
                Task_status.objects.get_or_create(
                    user_task=user_task,
                    old_status=current_status,
                    new_status=new_status
                )
                total_statuses += 1
                current_status = new_status

    print(f"Created {total_statuses} task statuses.")
