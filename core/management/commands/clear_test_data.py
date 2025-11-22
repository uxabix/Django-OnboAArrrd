from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction
from accounts.models import CustomUser
from onboarding.models import (
    Badges, User_badges, Competency_paths, Reports, User_paths,
    Task_types, Tasks, User_tasks, Task_status, Task_type_text,
    Task_type_quiz, Quizzes, Quiz_question, Quiz_answers, User_grade
)

class Command(BaseCommand):
    help = "Deletes all test data related to users in the TestUsers group"

    def handle(self, *args, **options):
        group_name = "TestUsers"
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Group '{group_name}' not found."))
            return

        users = CustomUser.objects.filter(groups=group)
        if not users.exists():
            self.stdout.write(self.style.WARNING("No test users found."))
            return

        with transaction.atomic():
            # Delete onboarding related data
            User_grade.objects.filter(reviewer__in=users).delete()
            User_grade.objects.filter(reviewed__in=users).delete()
            Task_status.objects.filter(user_task__user_id__in=users).delete()
            User_tasks.objects.filter(user_id__in=users).delete()
            User_paths.objects.filter(user__in=users).delete()
            Reports.objects.filter(user__in=users).delete()
            Reports.objects.filter(generated_by__in=users).delete()
            User_badges.objects.filter(user__in=users).delete()

            # Finally delete users
            users.delete()

        self.stdout.write(self.style.SUCCESS("All test user data deleted successfully."))
