"""``__str__`` helpers that do not touch related managers."""

from onboarding.models import (
    Badges,
    Competency_paths,
    Quiz_answers,
    Quiz_question,
    Task_type_text,
    Task_types,
    Tasks,
)


def test_badges_str():
    assert str(Badges(name="Starter", points=1, description="")) == "Starter"


def test_competency_paths_str():
    assert str(Competency_paths(name="Path A", description="Desc")) == "Path A"


def test_task_types_str():
    assert str(Task_types(task_type="Quiz")) == "Quiz"


def test_tasks_str():
    assert str(Tasks(title="Read docs")) == "Read docs"


def test_task_type_text_str():
    assert str(Task_type_text(content="Hello")) == "Hello"


def test_quiz_question_and_answer_str():
    question = Quiz_question(question="Q1?")
    assert str(question) == "Q1?"
    answer = Quiz_answers(answer="A1")
    assert str(answer) == "A1"
