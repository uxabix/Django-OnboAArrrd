from onboarding.models import Badges
import random

def run(count=10, group=None):
    for i in range(1, count + 1):
        badge = Badges.objects.create(
            name=f"Badge {i}",
            description=f"This is description for Badge {i}",
            points=random.randint(5, 100),
        )
        print(f"Created badge: {badge.name}")

    print(f"Created {count} badges.")
