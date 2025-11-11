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


class User_badges(models.Model):
    user_badge_id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_badges")
    badge = models.ForeignKey(Badges, on_delete=models.CASCADE)


class Competency_paths(models.Model):
    path_id = models.IntegerField(primary_key=True)
    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="competency_paths")
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Reports(models.Model):
    report_id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reports_received")
    generated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reports_generated")
    created_at = models.DateTimeField(auto_now_add=True)
    file_path = models.CharField(max_length=500)


class User_paths(models.Model):
    user_path_id = models.IntegerField(primary_key=True)
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="assigned_paths")
    path = models.ForeignKey(Competency_paths, on_delete=models.CASCADE, related_name="user_paths")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="user_paths")
    assigned_at = models.DateTimeField(auto_now_add=True)


class Tasks(models.Model):
    task_id = models.IntegerField(primary_key=True)
    path = models.ForeignKey(Competency_paths, on_delete=models.CASCADE, related_name="competency_path")
    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="mentor_tasks")
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="assigned_tasks")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()

    def __str__(self):
        return self.title


class Task_status(models.Model):
    status_id = models.IntegerField(primary_key=True)
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="statuses")
    changed_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="status_changes")
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    change_date = models.DateField(auto_now=True)


class Mentor_grade(models.Model):
    grade_id = models.IntegerField(primary_key=True)
    mentor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="mentor_grades")
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reviewer_grades")
    task = models.ForeignKey(Tasks, on_delete=models.CASCADE, related_name="mentor_grades")
