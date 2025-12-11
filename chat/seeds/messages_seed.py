import random
from django.contrib.auth import get_user_model
from chat.models import Messages

User = get_user_model()

def run(count=50, group=None):
    # Pobierz użytkowników, którzy mają mentora
    users_with_mentor = User.objects.filter(mentor__isnull=False)

    if not users_with_mentor.exists():
        print("Brak użytkowników z przypisanym mentorem.")
        return

    print(f"Tworzę wiadomości dla {users_with_mentor.count()} użytkowników...")

    for user in users_with_mentor:
        mentor = user.mentor

        # Tworzymy wiadomości od studenta do mentora
        for i in range(1, count + 1):
            Messages.objects.create(
                sender=user,
                receiver=mentor,
                text=f"Message {i} od {user.email} → {mentor.email}"
            )

        # Tworzymy wiadomości od mentora do studenta
        for i in range(1, count + 1):
            Messages.objects.create(
                sender=mentor,
                receiver=user,
                text=f"Odpowiedź {i} od {mentor.email} → {user.email}"
            )

        print(f"✓ Dodano {count*2} wiadomości dla użytkownika {user.email}")

    print("Seedowanie wiadomości zakończone.")
