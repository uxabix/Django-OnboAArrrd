from importlib import import_module

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from .seed import SEEDERS


DEMO_ORDER = [
    "roles",
    "users",
    "badges",
    "paths",
    "task_types",
    "tasks",
    "quiz",
    "user_paths",
    "user_tasks",
    "task_status",
    "grades",
    "reports",
    "messages",
]


class Command(BaseCommand):
    help = "Seed a compact, realistic demo dataset (around 10 users)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-first",
            action="store_true",
            help="Run clear_test_data before seeding demo data.",
        )

    def handle(self, *args, **options):
        if options["reset_first"]:
            from django.core.management import call_command

            self.stdout.write(self.style.NOTICE("Running cleanup before demo seed..."))
            call_command("clear_test_data")

        group, created = Group.objects.get_or_create(name="TestUsers")
        if created:
            self.stdout.write(self.style.SUCCESS("Created group 'TestUsers'"))

        self.stdout.write(self.style.NOTICE("Seeding compact demo dataset..."))
        for module_name in DEMO_ORDER:
            module_path = SEEDERS[module_name]
            self.stdout.write(self.style.NOTICE(f"Running demo seeder: {module_name}"))
            module = import_module(module_path)
            if hasattr(module, "run"):
                module.run(count=10, group=group)

        self.stdout.write(self.style.SUCCESS("Demo seed complete."))
