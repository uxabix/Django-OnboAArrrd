"""Database models for onboarding artifacts (paths, tasks, quizzes, grades)."""

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

import django.db.models.signals as signals
from django.dispatch import receiver


class Badges(models.Model):
    """Gamification badge that can be awarded to users."""

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
    """Association between a user and a badge they earned."""

    user_badge_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_badges", blank=True)
    badge = models.ForeignKey(Badges, on_delete=models.CASCADE, blank=True)
    awarder_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "User Badge"
        verbose_name_plural = "User Badges"


class Competency_paths(models.Model):
    """Reusable learning track composed of ordered ``Tasks``."""

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
    """Binary or path-oriented artifact generated for a user by another user."""

    report_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reports_received", blank=True)
    generated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reports_generated", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=500)

    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"


class User_paths(models.Model):
    """Assignment linking a learner to a ``Competency_paths`` instance."""

    user_path_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_paths", blank=True, null=True)
    path = models.ForeignKey(Competency_paths, on_delete=models.CASCADE, related_name="user_paths", blank=True, null=True)
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="assigned_paths", blank=True, null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Path"
        verbose_name_plural = "User Paths"

class Task_types(models.Model):
    """High-level discriminator for task presentation (text, quiz, etc.)."""

    task_type_id = models.BigAutoField(primary_key=True)
    task_type = models.CharField(max_length=50)

    def __str__(self):
        return self.task_type

    class Meta:
        verbose_name = "Task_type"
        verbose_name_plural = "Task_types"


class Tasks(models.Model):
    """Catalog task optionally nested under a competency path."""

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
    """Concrete assignment of a ``Tasks`` row to a learner with a deadline.

    ``APPROACHING_THRESHOLD_DAYS`` controls how many days before ``deadline`` a
    task is treated as approaching for reminders.
    """

    user_tasks_id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="user_to_task")
    task_id = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="task_to_user", blank=True)
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True, related_name="who_assigned")

    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()

    # Liczba dni od deadline'u, kiedy zadanie traktujemy jako "zbliżające się" (np. dla powiadomień)
    APPROACHING_THRESHOLD_DAYS = 3

    class Meta:
        verbose_name = "User Task"
        verbose_name_plural = "User Tasks"

    @property
    def latest_status(self):
        """Return the newest ``Task_status`` row using prefetched data when possible.

        Returns:
            Task_status | None: Latest status or ``None`` when no history exists.
        """
        # Wykorzystujemy already-fetched prefetch jeśli dostępny
        statuses = list(self.statuses.all())
        if not statuses:
            return None
        return sorted(statuses, key=lambda s: s.change_date, reverse=True)[0]

    @property
    def current_status(self):
        """Latest ``Task_status.Status`` value or the default to-do state.

        Returns:
            str: Text choice value from ``Task_status.Status``.
        """
        latest = self.latest_status
        if latest is None:
            return Task_status.Status.DO_ZROBIENIA
        return latest.new_status

    @property
    def is_completed(self):
        """Whether the workflow reached the completed terminal state.

        Returns:
            bool: ``True`` when ``current_status`` is ``UKONCZONE``.
        """
        return self.current_status == Task_status.Status.UKONCZONE

    @property
    def is_submitted(self):
        """True when the learner submitted the task or it was completed.

        Returns:
            bool: ``True`` for verification or completed states.
        """
        return self.current_status in (
            Task_status.Status.DO_WERYFIKACJI,
            Task_status.Status.UKONCZONE,
        )

    @property
    def submission_date(self):
        """First timestamp when the task entered verification or completion.

        Returns:
            datetime.date | None: ``change_date`` from the earliest qualifying
            ``Task_status`` row, if any.
        """
        statuses = sorted(self.statuses.all(), key=lambda s: s.change_date)
        for status in statuses:
            if status.new_status in (
                Task_status.Status.DO_WERYFIKACJI,
                Task_status.Status.UKONCZONE,
            ):
                return status.change_date
        return None

    @property
    def is_overdue(self):
        """Whether the deadline passed without submission or completion.

        Returns:
            bool: ``True`` when still unsubmitted and ``deadline`` is in the past.
        """
        if self.is_submitted:
            return False
        return self.deadline < timezone.now().date()

    @property
    def days_until_deadline(self):
        """Signed day delta between today and ``deadline``.

        Returns:
            int: Negative values indicate a missed deadline in calendar days.
        """
        return (self.deadline - timezone.now().date()).days

    @property
    def is_approaching_deadline(self):
        """True when unsubmitted and the deadline is within the threshold window.

        Returns:
            bool: Uses ``APPROACHING_THRESHOLD_DAYS`` for the inclusive window.
        """
        if self.is_submitted:
            return False
        days = self.days_until_deadline
        return 0 <= days <= self.APPROACHING_THRESHOLD_DAYS

    @property
    def submitted_on_time(self):
        """Whether the first submission happened on or before ``deadline``.

        Returns:
            bool: ``False`` when no submission exists.
        """
        sub = self.submission_date
        return sub is not None and sub <= self.deadline

    @property
    def submitted_late(self):
        """Whether the first submission happened strictly after ``deadline``.

        Returns:
            bool: ``False`` when no submission exists.
        """
        sub = self.submission_date
        return sub is not None and sub > self.deadline

    @property
    def deadline_state(self):
        """Coarse UI state summarizing timeliness for dashboards.

        Returns:
            str: One of ``on_time``, ``late``, ``overdue``, ``approaching``,
            ``on_track`` describing the combination of submission and deadline.
        """
        if self.is_submitted:
            return 'on_time' if self.submitted_on_time else 'late'
        if self.is_overdue:
            return 'overdue'
        if self.is_approaching_deadline:
            return 'approaching'
        return 'on_track'


class Task_status(models.Model):
    """Immutable history row capturing a transition between workflow states."""

    task_status_id = models.BigAutoField(primary_key=True)
    user_task = models.ForeignKey(User_tasks, on_delete=models.CASCADE, related_name="statuses", blank=True, null=True)

    class Status(models.TextChoices):
        """Polish-facing workflow labels stored in the database."""

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
    """Free-text payload attached to a text-style ``Tasks`` row."""

    task_text_id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="text_task_type")

    content = models.TextField(max_length=500)

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = "Task Type Text"
        verbose_name_plural = "Tasks Type Text"

class Task_type_quiz(models.Model):
    """Marker linking a task to its ``Quizzes`` subtree."""

    task_quiz_id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="quiz_task_type")

    class Meta:
        verbose_name = "Task Type Quiz"
        verbose_name_plural = "Tasks Type Quiz"

class Quizzes(models.Model):
    """Top-level quiz container for a task."""

    quiz_id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="quiz_task")

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

class Quiz_question(models.Model):
    """Single question belonging to a ``Quizzes`` instance."""

    question_id = models.BigAutoField(primary_key=True)
    quiz = models.ForeignKey(Quizzes, on_delete=models.CASCADE, related_name="question_to_quiz")

    question = models.CharField(max_length=255)

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "Quiz question"
        verbose_name_plural = "Quiz questions"

class Quiz_answers(models.Model):
    """Answer option row with tri-state correctness for quizzes."""

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
    """Mentor-provided grade for a specific ``User_tasks`` attempt."""

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


@receiver(signals.post_save, sender=Task_status)
def update_mentor_stars(sender, instance, created, **kwargs):
    """Increment mentor ``stars`` when a mentee task reaches completion.

    Args:
        sender: The ``Task_status`` model class.
        instance: Saved ``Task_status`` row.
        created: Whether this hook runs for a newly inserted row.
        **kwargs: Additional Django signal kwargs (unused).
    """
    if not created:
        if instance.new_status == Task_status.Status.UKONCZONE:
            mentor = instance.user_task.assigned_by
            if mentor:
                mentor.stars += 1
                mentor.save(update_fields=['stars'])
