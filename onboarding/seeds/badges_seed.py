from onboarding.models import Badges

def run(count=10, group=None):
    badges_data = [
        ("Fast Starter", "Szybkie wykonanie pierwszych zadan onboardingowych.", 20),
        ("Quality Keeper", "Wysoka jakosc realizacji zadan.", 40),
        ("Reliable Teammate", "Terminowosc i dobra komunikacja z mentorem.", 30),
        ("Mentor Favorite", "Stabilne postepy i proaktywna postawa.", 50),
    ]
    created = 0
    for name, description, points in badges_data:
        _, was_created = Badges.objects.get_or_create(
            name=name,
            defaults={"description": description, "points": points},
        )
        if was_created:
            created += 1
            print(f"Created badge: {name}")

    print(f"Badges prepared. Newly created: {created}.")
