from django.db import models
from django.contrib.auth import get_user_model

CustomUser = get_user_model()


class Badges(models.Model):
    badge_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    points = models.IntegerField()
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"


class User_badges(models.Model):
    user_badge_id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_badges", blank=True)
    badge = models.ForeignKey(Badges, on_delete=models.CASCADE, blank=True)

    class Meta:
        verbose_name = "User Badge"
        verbose_name_plural = "User Badges"


class Competency_paths(models.Model):
    path_id = models.IntegerField(primary_key=True)
    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="competency_paths", blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Competency Path"
        verbose_name_plural = "Competency Paths"


class Reports(models.Model):
    report_id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reports_received", blank=True)
    generated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reports_generated", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=500)

    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"


class User_paths(models.Model):
    user_path_id = models.IntegerField(primary_key=True)
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="assigned_paths", blank=True)
    path = models.ForeignKey(Competency_paths, on_delete=models.CASCADE, related_name="user_paths", blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_paths", blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Path"
        verbose_name_plural = "User Paths"


class Tasks(models.Model):
    task_id = models.IntegerField(primary_key=True)
    path = models.ForeignKey(Competency_paths, on_delete=models.CASCADE, related_name="competency_path", blank=True)
    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="mentor_tasks", blank=True)
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="assigned_tasks", blank=True)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"


class Task_status(models.Model):
    status_id = models.IntegerField(primary_key=True)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="statuses", blank=True)
    changed_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="status_changes", blank=True)
    old_status = models.CharField(max_length=50, blank=True)
    new_status = models.CharField(max_length=50, blank=True)
    change_date = models.DateField(auto_now=True)

    class Meta:
        verbose_name = "Task Status"
        verbose_name_plural = "Task Statuses"


class Mentor_grade(models.Model):
    grade_id = models.IntegerField(primary_key=True)
    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="mentor_grades", blank=True)
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reviewer_grades", blank=True)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="mentor_grades", blank=True)

    class Meta:
        verbose_name = "Mentor Grade"
        verbose_name_plural = "Mentor Grades"
