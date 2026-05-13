"""Attach randomized quiz graphs to quiz-type tasks."""

import random

from onboarding.models import Tasks, Quizzes, Quiz_question, Quiz_answers

def run(count=1, group=None):
    tasks = list(Tasks.objects.all())
    if not tasks:
        print("No tasks found. Please seed tasks first.")
        return

    question_counter = 1
    answer_counter = 1

    for task in tasks:
        if random.random() > 0.4: # Skip 60% of tasks
            continue
        quiz = Quizzes.objects.create(task=task)

        for q in range(count):  # Create count of questions for each task
            question = Quiz_question.objects.create(
                quiz=quiz,
                question=f"Question {question_counter} for {task.title}"
            )

            # Create answers for each question
            for i in range(random.randint(2, 4)):
                Quiz_answers.objects.create(
                    question=question,
                    answer=f"Answer {answer_counter}",
                    correct=(i == 0)
                )
                answer_counter += 1

            question_counter += 1

    print(f"Created {question_counter - 1} quiz questions and {answer_counter - 1} answers.")
