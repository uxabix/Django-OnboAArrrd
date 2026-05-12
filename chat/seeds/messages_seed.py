import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from chat.models import Messages

User = get_user_model()

def run(count=6, group=None):
    # Pobierz użytkowników, którzy mają mentora
    users_with_mentor = User.objects.filter(mentor__isnull=False)

    if not users_with_mentor.exists():
        print("No users found with assigned mentors.")
        return

    print(f"Creating messages for {users_with_mentor.count()} users...")

    for user in users_with_mentor:
        mentor = user.mentor

        for i in range(1, min(count, 6) + 1):
            # losowa data w ciągu ostatnich 3 miesięcy
            random_days = random.randint(0, 90)
            random_seconds = random.randint(0, 86400)
            random_datetime = timezone.now() - timedelta(days=random_days, seconds=random_seconds)

            # wiadomość od pracownika do mentora
            Messages.objects.create(
                sender=user,
                receiver=mentor,
                text=f"Message {i}",
                sent_at=random_datetime
            )

            # losowa data dla odpowiedzi mentora
            random_days = random.randint(0, 90)
            random_seconds = random.randint(0, 86400)
            random_datetime = timezone.now() - timedelta(days=random_days, seconds=random_seconds)

            # wiadomość od mentora do pracownika
            Messages.objects.create(
                sender=mentor,
                receiver=user,
                text=f"Response {i}",
                sent_at=random_datetime
            )

        print(f"Added {min(count, 6) * 2} messages for user {user.email}")

    print("Seeding completed.")
