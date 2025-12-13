from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

CustomUser = get_user_model()


class Badges(models.Model):
    badge_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    points = models.IntegerField()
    description = models.TextField()
    icon = models.ImageField(upload_to='badge_icons/', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"


class User_badges(models.Model):
    user_badge_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_badges", blank=True)
    badge = models.ForeignKey(Badges, on_delete=models.CASCADE, blank=True)
    awarder_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "User Badge"
        verbose_name_plural = "User Badges"


class Competency_paths(models.Model):
    path_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Competency Path"
        verbose_name_plural = "Competency Paths"


class Reports(models.Model):
    report_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reports_received", blank=True)
    generated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reports_generated", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=500)

    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"


class User_paths(models.Model):
    user_path_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_paths", blank=True, null=True)
    path = models.ForeignKey(Competency_paths, on_delete=models.CASCADE, related_name="user_paths", blank=True, null=True)
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="assigned_paths", blank=True, null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Path"
        verbose_name_plural = "User Paths"

class Task_types(models.Model):
    task_type_id = models.BigAutoField(primary_key=True)
    task_type = models.CharField(max_length=50)

    def __str__(self):
        return self.task_type

    class Meta:
        verbose_name = "Task_type"
        verbose_name_plural = "Task_types"


class Tasks(models.Model):
    task_id = models.BigAutoField(primary_key=True)
    path = models.ForeignKey(Competency_paths, on_delete=models.CASCADE, related_name="competency_path", blank=True, null=True)
    task_type = models.ForeignKey(Task_types, blank=True, null=True, on_delete=models.SET_NULL)

    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    path_order = models.IntegerField(null=True, blank=True)
    public = models.BooleanField(default=False, blank=True, null=True)
    need_verification = models.BooleanField(default=True, blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

class User_tasks(models.Model):
    user_tasks_id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="user_to_task")
    task_id = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="task_to_user", blank=True)
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True, related_name="who_assigned")

    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()

    class Meta:
        verbose_name = "User Task"
        verbose_name_plural = "User Tasks"


class Task_status(models.Model):
    task_status_id = models.BigAutoField(primary_key=True)
    user_task = models.ForeignKey(User_tasks, on_delete=models.CASCADE, related_name="statuses", blank=True, null=True)

    class Status(models.TextChoices):
        DO_ZROBIENIA = "do zrobienia"
        W_TRAKCIE = "w trakcie"
        DO_WERYFIKACJI = "do weryfikacji"
        UKONCZONE = "ukończone"

    old_status = models.CharField(
        max_length=50,
        choices=Status.choices,
        # models.SET_NULL предназначен для on_delete у ForeignKey, а не как default
        # Для отсутствующего предыдущего статуса используем None
        default=None,
        blank=True,
        null=True,
    )
    new_status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.DO_ZROBIENIA,
        blank=True,
    )
    change_date = models.DateField(auto_now=True)

    class Meta:
        verbose_name = "Task Status"
        verbose_name_plural = "Task Statuses"

class Task_type_text(models.Model):
    task_text_id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="text_task_type")

    content = models.TextField(max_length=500)

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = "Task Type Text"
        verbose_name_plural = "Tasks Type Text"

class Task_type_quiz(models.Model):
    task_quiz_id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="quiz_task_type")

    class Meta:
        verbose_name = "Task Type Quiz"
        verbose_name_plural = "Tasks Type Quiz"

class Quizzes(models.Model):
    quiz_id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="quiz_task")

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

class Quiz_question(models.Model):
    question_id = models.BigAutoField(primary_key=True)
    quiz = models.ForeignKey(Quizzes, on_delete=models.CASCADE, related_name="question_to_quiz")

    question = models.CharField(max_length=255)

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "Quiz question"
        verbose_name_plural = "Quiz questions"

class Quiz_answers(models.Model):
    answer_id = models.BigAutoField(primary_key=True)
    question = models.ForeignKey(Quiz_question, on_delete=models.CASCADE, related_name="answer_to_question")

    answer = models.CharField(max_length=500)
    # default=models.SET_NULL некорректен для BooleanField — используем None при трёхсостоянии
    correct = models.BooleanField(default=None, blank=True, null=True)

    def __str__(self):
        return self.answer
    
    class Meta:
        verbose_name = "Quiz answer"
        verbose_name_plural = "Quiz answers"

class User_grade(models.Model):
    grade_id = models.BigAutoField(primary_key=True)
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reviewer_grades", blank=True)
    reviewed = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reviewed_grades", blank=True)
    user_task = models.ForeignKey(User_tasks, on_delete=models.CASCADE, related_name="mentor_grades", blank=True)

    rating = models.IntegerField()
    description = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Grade"
        verbose_name_plural = "User Grades"
