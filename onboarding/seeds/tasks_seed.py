"""Seed task types, catalog tasks, and link them to competency paths."""

from onboarding.models import Task_types, Tasks, Competency_paths

def run(count=6, group=None):
    task_type_text, _ = Task_types.objects.get_or_create(task_type="Text")
    task_type_quiz, _ = Task_types.objects.get_or_create(task_type="Quiz")

    paths = {p.name: p for p in Competency_paths.objects.all()}
    if not paths:
        print("No competency paths found. Please seed paths first.")
        return

    tasks_data = [
        ("Python Backend Onboarding", task_type_text, 1, "Poznaj architekture projektu", True),
        ("Python Backend Onboarding", task_type_text, 2, "Uruchom projekt lokalnie i opisz kroki", True),
        ("Python Backend Onboarding", task_type_quiz, 3, "Quiz: Django fundamentals", True),
        ("Komunikacja i Procesy", task_type_text, 1, "Przygotuj status tygodniowy", False),
        ("Komunikacja i Procesy", task_type_text, 2, "Symulacja code review", True),
        ("Komunikacja i Procesy", task_type_quiz, 3, "Quiz: workflow zespolu", False),
        ("Bezpieczenstwo i Jakosc", task_type_text, 1, "Checklista bezpieczenstwa PR", True),
        ("Bezpieczenstwo i Jakosc", task_type_text, 2, "Dodaj testy regresyjne", True),
        ("Bezpieczenstwo i Jakosc", task_type_quiz, 3, "Quiz: OWASP basics", True),
    ]

    created = 0
    for path_name, task_type, path_order, title, is_public in tasks_data:
        path = paths.get(path_name)
        if path is None:
            continue
        _, was_created = Tasks.objects.get_or_create(
            path=path,
            title=title,
            defaults={
                "task_type": task_type,
                "description": f"Demo task: {title}",
                "path_order": path_order,
                "public": is_public,
                "need_verification": True,
            },
        )
        if was_created:
            created += 1
            print(f"Created task: {title} in path: {path.name}")

    print(f"Tasks prepared. Newly created: {created}.")
