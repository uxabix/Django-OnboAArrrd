import random
from onboarding.models import Reports
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

def run(count=10, group=None):
    users = list(CustomUser.objects.all())
    if len(users) < 2:
        print("Need at least 2 users to generate reports.")
        return

    reports_created = 0

    for i in range(min(count, 8)):
        generated_by = random.choice(users)
        user = random.choice([u for u in users if u != generated_by])

        Reports.objects.create(
            user=user,
            generated_by=generated_by,
            file_path=f"/tmp/report_{generated_by.id}_{user.id}_{reports_created}.pdf"
        )
        reports_created += 1

    print(f"Created {reports_created} reports.")
