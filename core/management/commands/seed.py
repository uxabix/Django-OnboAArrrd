from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from importlib import import_module

SEEDERS_ORDER = [
    "roles",
    "users",
    "badges",
    "paths",
    "task_types",
    "tasks",
    "quiz",
    "user_paths",
    "user_tasks",
    "reports",
]

SEEDERS = {
    "roles": "accounts.seeds.roles_seed",
    "users": "accounts.seeds.users_seed",
    "badges": "oboarding.seeds.badges_seed",
    "paths": "oboarding.seeds.competency_paths_seed",
    "task_types": "oboarding.seeds.tasks_seed",
    "tasks": "oboarding.seeds.tasks_seed",
    "quiz": "oboarding.seeds.quiz_seed",
    "user_paths": "oboarding.seeds.user_paths_seed",
    "user_tasks": "oboarding.seeds.user_tasks_seed",
    "reports": "oboarding.seeds.reports_seed",
}

class Command(BaseCommand):
    help = "Seed database with test data"

    def add_arguments(self, parser):
        parser.add_argument(
            'modules', nargs='*', type=str,
            help="Seed modules to run or 'all'"
        )
        parser.add_argument(
            '--count', type=int, default=10,
            help="Number of objects to create"
        )

    def handle(self, *args, **options):
        modules = options['modules'] or ['all']
        count = options['count']

        # Создаем группу TestUsers
        group, created = Group.objects.get_or_create(name="TestUsers")
        if created:
            self.stdout.write(self.style.SUCCESS("Created group 'TestUsers'"))

        if 'all' in modules:
            modules_to_run = SEEDERS_ORDER
        else:
            modules_to_run = [m for m in modules if m in SEEDERS]
            invalid = [m for m in modules if m not in SEEDERS]
            if invalid:
                self.stdout.write(self.style.WARNING(f"Invalid seed modules: {invalid}"))

        for module_name in modules_to_run:
            self.stdout.write(self.style.NOTICE(f"Running seeder: {module_name}"))
            module_path = SEEDERS[module_name]
            try:
                module = import_module(module_path)
                if hasattr(module, "run"):
                    module.run(count=count, group=group)
                else:
                    self.stdout.write(self.style.WARNING(f"No run() in {module_name}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error running {module_name}: {e}"))

        self.stdout.write(self.style.SUCCESS("Seeding complete!"))
