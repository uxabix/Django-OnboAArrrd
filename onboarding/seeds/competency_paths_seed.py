from onboarding.models import Competency_paths

def run(count=10, group=None):
    paths_data = [
        ("Python Backend Onboarding", "Podstawy stacku backendowego i standardy pracy zespolu."),
        ("Komunikacja i Procesy", "Praca z zespolem, proces code review i raportowanie postepu."),
        ("Bezpieczenstwo i Jakosc", "Bezpieczenstwo aplikacji, testowanie i jakosc wdrozen."),
    ]
    created = 0
    for name, description in paths_data:
        _, was_created = Competency_paths.objects.get_or_create(
            name=name,
            defaults={"description": description},
        )
        if was_created:
            created += 1
            print(f"Created competency path: {name}")

    print(f"Competency paths prepared. Newly created: {created}.")
