from onboarding.models import Task_status, User_grade, User_tasks
def run(count=1, group=None):
    user_tasks = list(User_tasks.objects.select_related("assigned_by", "user_id").prefetch_related("statuses"))
    if not user_tasks:
        print("No user tasks found. Please seed user_tasks first.")
        return

    total_grades = 0
    grade_descriptions = [
        (5, "Bardzo dobra jakosc i samodzielna realizacja."),
        (4, "Dobre wykonanie, drobne uwagi do poprawy."),
        (3, "Zadanie wykonane, ale wymaga dopracowania."),
    ]

    for idx, user_task in enumerate(user_tasks):
        if not user_task.assigned_by or not user_task.user_id:
            continue
        if user_task.current_status != Task_status.Status.UKONCZONE:
            continue
        if user_task.assigned_by_id == user_task.user_id_id:
            continue

        rating, description = grade_descriptions[idx % len(grade_descriptions)]
        _, created = User_grade.objects.get_or_create(
            reviewer=user_task.assigned_by,
            reviewed=user_task.user_id,
            user_task=user_task,
            defaults={"rating": rating, "description": description},
        )
        if created:
            total_grades += 1

    print(f"Created {total_grades} user grades.")
