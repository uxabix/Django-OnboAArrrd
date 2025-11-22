from onboarding.models import Tasks, Quizzes, Quiz_question, Quiz_answers

def run(count=1, group=None):
    tasks = list(Tasks.objects.all())
    if not tasks:
        print("No tasks found. Please seed tasks first.")
        return

    question_counter = 1
    answer_counter = 1

    for task in tasks:
        # Создаем quiz для каждой задачи
        quiz = Quizzes.objects.create(task=task)

        for q in range(count):  # создаем count вопросов на задачу
            question = Quiz_question.objects.create(
                quiz=quiz,
                question=f"Question {question_counter} for {task.title}"
            )

            # Создаем 4 варианта ответов, первый правильный
            for i in range(4):
                Quiz_answers.objects.create(
                    question=question,
                    answer=f"Answer {answer_counter}",
                    correct=(i == 0)
                )
                answer_counter += 1

            question_counter += 1

    print(f"Created {question_counter - 1} quiz questions and {answer_counter - 1} answers.")
