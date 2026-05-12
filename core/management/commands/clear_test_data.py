from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from accounts.models import CustomUser
from onboarding.models import (
    Badges, User_badges, Competency_paths, Reports, User_paths,
    Task_types, Tasks, User_tasks, Task_status, Task_type_text,
    Task_type_quiz, Quizzes, Quiz_question, Quiz_answers, User_grade
)
from chat.models import Messages


DEMO_PATH_NAMES = [
    "Python Backend Onboarding",
    "Komunikacja i Procesy",
    "Bezpieczenstwo i Jakosc",
]
DEMO_TASK_TITLES = [
    "Poznaj architekture projektu",
    "Uruchom projekt lokalnie i opisz kroki",
    "Quiz: Django fundamentals",
    "Przygotuj status tygodniowy",
    "Symulacja code review",
    "Quiz: workflow zespolu",
    "Checklista bezpieczenstwa PR",
    "Dodaj testy regresyjne",
    "Quiz: OWASP basics",
]
DEMO_BADGE_NAMES = ["Fast Starter", "Quality Keeper", "Reliable Teammate", "Mentor Favorite"]

class Command(BaseCommand):
    help = "Delete seeded demo/legacy test data (users + onboarding/chat artifacts)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-users",
            action="store_true",
            help="Keep detected seed users and remove only related seeded artifacts.",
        )

    def handle(self, *args, **options):
        keep_users = options["keep_users"]
        group_name = "TestUsers"
        group = Group.objects.filter(name=group_name).first()

        users_qs = CustomUser.objects.filter(
            Q(groups=group) if group else Q(pk__in=[]),
            is_superuser=False,
        ) | CustomUser.objects.filter(
            Q(email__iendswith="@test.com") | Q(email__iendswith="@onboard.local"),
            is_superuser=False,
        )
        users = users_qs.distinct()

        with transaction.atomic():
            User_grade.objects.filter(Q(reviewer__in=users) | Q(reviewed__in=users)).delete()
            Task_status.objects.filter(Q(user_task__user_id__in=users) | Q(user_task__assigned_by__in=users)).delete()
            Messages.objects.filter(Q(sender__in=users) | Q(receiver__in=users)).delete()
            User_tasks.objects.filter(Q(user_id__in=users) | Q(assigned_by__in=users)).delete()
            User_paths.objects.filter(Q(user__in=users) | Q(assigned_by__in=users)).delete()
            Reports.objects.filter(Q(user__in=users) | Q(generated_by__in=users)).delete()
            User_badges.objects.filter(user__in=users).delete()

            # Legacy + demo seeded objects not always tied to users
            seeded_tasks_qs = Tasks.objects.filter(
                Q(title__startswith="Task ")
                | Q(description__startswith="This is description for Task ")
                | Q(description__startswith="Demo task:")
                | Q(title__in=DEMO_TASK_TITLES)
            )
            Task_status.objects.filter(user_task__task_id__in=seeded_tasks_qs).delete()
            Messages.objects.filter(Q(user_task__task_id__in=seeded_tasks_qs)).delete()
            User_grade.objects.filter(user_task__task_id__in=seeded_tasks_qs).delete()
            User_tasks.objects.filter(task_id__in=seeded_tasks_qs).delete()
            Task_type_text.objects.filter(task__in=seeded_tasks_qs).delete()
            Task_type_quiz.objects.filter(task__in=seeded_tasks_qs).delete()
            Quizzes.objects.filter(task__in=seeded_tasks_qs).delete()
            seeded_tasks_qs.delete()

            seeded_paths_qs = Competency_paths.objects.filter(
                Q(name__startswith="Competency Path ") | Q(name__in=DEMO_PATH_NAMES)
            )
            Messages.objects.filter(user_path__path__in=seeded_paths_qs).delete()
            User_paths.objects.filter(path__in=seeded_paths_qs).delete()
            Tasks.objects.filter(path__in=seeded_paths_qs).delete()
            seeded_paths_qs.delete()

            Badges.objects.filter(Q(name__startswith="Badge ") | Q(name__in=DEMO_BADGE_NAMES)).delete()
            for task_type_name in ["Text", "Quiz"]:
                tt = Task_types.objects.filter(task_type=task_type_name).first()
                if tt and not Tasks.objects.filter(task_type=tt).exists():
                    tt.delete()

            if not keep_users:
                deleted_users_count, _ = users.delete()
                self.stdout.write(self.style.SUCCESS(f"Deleted seed users and related data. Users removed: {deleted_users_count}"))
            else:
                self.stdout.write(self.style.SUCCESS("Deleted seeded artifacts and kept users (--keep-users)."))

            if group and not group.user_set.exists():
                group.delete()

        self.stdout.write(self.style.SUCCESS("Seed cleanup completed."))
