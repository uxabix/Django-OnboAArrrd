from onboarding.models import Competency_paths

def run(count=10, group=None):
    for i in range(1, count + 1):
        path = Competency_paths.objects.create(
            name=f"Competency Path {i}",
            description=f"This is description for Competency Path {i}",
        )
        print(f"Created competency path: {path.name}")

    print(f"Created {count} competency paths.")
