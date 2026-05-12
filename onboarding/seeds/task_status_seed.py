from datetime import timedelta
from django.utils import timezone
from onboarding.models import Task_status, User_tasks

def run(count=1, group=None):
    user_tasks = list(User_tasks.objects.all())
    if not user_tasks:
        print("No user tasks found. Please seed user_tasks first.")
        return

    total_statuses = 0
    today = timezone.now().date()

    scenarios = [
        # oddane w terminie (deadline wczoraj, ukonczone 2 dni temu)
        [Task_status.Status.DO_ZROBIENIA, Task_status.Status.W_TRAKCIE, Task_status.Status.DO_WERYFIKACJI, Task_status.Status.UKONCZONE],
        # oddane po terminie
        [Task_status.Status.DO_ZROBIENIA, Task_status.Status.W_TRAKCIE, Task_status.Status.DO_WERYFIKACJI, Task_status.Status.UKONCZONE],
        # przeterminowane, brak oddania
        [Task_status.Status.DO_ZROBIENIA, Task_status.Status.W_TRAKCIE],
        # aktywne w trakcie
        [Task_status.Status.DO_ZROBIENIA, Task_status.Status.W_TRAKCIE],
        # nowe do zrobienia
        [Task_status.Status.DO_ZROBIENIA],
    ]

    for idx, user_task in enumerate(user_tasks):
        scenario = scenarios[idx % len(scenarios)]
        user_task.statuses.all().delete()

        for step_idx, status_value in enumerate(scenario):
            old_status = scenario[step_idx - 1] if step_idx > 0 else None
            status = Task_status.objects.create(
                user_task=user_task,
                old_status=old_status,
                new_status=status_value,
            )
            # auto_now -> nadpisujemy recznie, aby terminowosc wygladala realistycznie
            custom_date = today - timedelta(days=max(0, len(scenario) - step_idx))
            if idx % len(scenarios) == 1 and status_value == Task_status.Status.UKONCZONE:
                custom_date = user_task.deadline + timedelta(days=2)
            if idx % len(scenarios) == 0 and status_value == Task_status.Status.UKONCZONE:
                custom_date = user_task.deadline - timedelta(days=1)
            Task_status.objects.filter(pk=status.pk).update(change_date=custom_date)
            total_statuses += 1

        if scenario[-1] == Task_status.Status.UKONCZONE and user_task.assigned_by:
            # Sprawiamy, ze ranking mentorow ma sensowne gwiazdki.
            user_task.assigned_by.stars += 1
            user_task.assigned_by.save(update_fields=["stars"])

    print(f"Created {total_statuses} task statuses.")
