from onboarding.models import Task_types, Tasks, Competency_paths

def run(count=6, group=None):
    task_types_data = ["Text", "Quiz"]
    for t in task_types_data:
        Task_types.objects.get_or_create(task_type=t)

    task_types = list(Task_types.objects.all())
    paths = list(Competency_paths.objects.all())
    if not paths:
        print("No competency paths found. Please seed paths first.")
        return

    task_counter = 1
    for path in paths:
        for i in range(count):
            task_type = task_types[i % len(task_types)]
            task = Tasks.objects.create(
                path=path,
                task_type=task_type,
                title=f"Task {task_counter}",
                description=f"This is description for Task {task_counter}",
                path_order=i + 1,
                public=True if i % 2 == 0 else False,
                need_verification=True,
            )
            print(f"Created task: {task.title} in path: {path.name}")
            task_counter += 1

    print(f"Created {task_counter - 1} tasks.")
