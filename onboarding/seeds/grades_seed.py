import random
from onboarding.models import User_grade, User_tasks
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

def run(count=1, group=None):
    user_tasks = list(User_tasks.objects.all())
    if not user_tasks:
        print("No user tasks found. Please seed user_tasks first.")
        return

    total_grades = 0

    # Create grades for mentor assignments
    for user_task in user_tasks:
        if user_task.assigned_by and user_task.user_id:
            # Check if mentor assigned task
            if user_task.assigned_by.role and user_task.assigned_by.role.name.lower() == "mentor":
                # Randomly assign grade
                if random.random() < 0.6:  # 60% will get a grade
                    rating = random.randint(1, 5)
                    descriptions = [
                        "Good job",
                        "Good, but You can do better.",
                        "Task completed with some issues.",
                        "You need to be more careful.",
                        "Great job!",
                        "Great way to complete the task!",
                    ]

                    User_grade.objects.get_or_create(
                        reviewer=user_task.assigned_by,
                        reviewed=user_task.user_id,
                        user_task=user_task,
                        defaults={
                            'rating': rating,
                            'description': random.choice(descriptions)
                        }
                    )
                    total_grades += 1

    print(f"Created {total_grades} user grades.")
