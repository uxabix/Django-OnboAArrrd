from accounts.models import Roles

def run(count=10, group=None):
    roles_data = [
        {"name": "Admin", "description": "Administrator with full access"},
        {"name": "Mentor", "description": "Mentor who guides students"},
        {"name": "Student", "description": "Regular student user"},
    ]

    for role in roles_data:
        obj, created = Roles.objects.get_or_create(name=role["name"], defaults={"description": role["description"]})
        if created:
            print(f"Created role: {role['name']}")
