"""Django admin registrations for onboarding models."""

from django.contrib import admin
from .models import (
    Badges,
    User_badges,
    Competency_paths,
    Reports,
    User_paths,
    Tasks,
    Task_status,
    User_grade,
    Task_types,
    Task_type_text,
    Task_type_quiz,
    Quizzes,
    Quiz_question,
    Quiz_answers,
    User_tasks
)
from django.utils.html import format_html

# ------------------------
# Badges
# ------------------------
class BadgesAdmin(admin.ModelAdmin):
    list_display = ('badge_id', 'name', 'points', 'description', 'icon_tag')
    search_fields = ('name',)
    ordering = ('badge_id',)

    def icon_tag(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="30" height="30" />', obj.icon.url)
        return "-"
    icon_tag.short_description = 'Icon'

# ------------------------
# User Badges
# ------------------------
class UserBadgesAdmin(admin.ModelAdmin):
    list_display = ('user_badge_id', 'user', 'badge', 'awarder_at')
    search_fields = ('user__email', 'badge__name')
    ordering = ('user_badge_id',)

# ------------------------
# Competency Paths
# ------------------------
class CompetencyPathsAdmin(admin.ModelAdmin):
    list_display = ('path_id', 'name', 'created_at')
    search_fields = ('name',)
    ordering = ('path_id',)

# ------------------------
# Reports
# ------------------------
class ReportsAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'user', 'generated_by', 'created_at', 'file_path')
    search_fields = ('user__email', 'generated_by__email')
    ordering = ('report_id',)

# ------------------------
# User Paths
# ------------------------
class UserPathsAdmin(admin.ModelAdmin):
    list_display = ('user_path_id', 'user', 'path', 'assigned_by', 'assigned_at')
    search_fields = ('user__email', 'path__name', 'assigned_by__email')
    ordering = ('user_path_id',)

# ------------------------
# Tasks
# ------------------------
class TasksAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'title', 'path', 'task_type', 'public', 'need_verification')
    search_fields = ('title', 'path__name', 'task_type__task_type')
    ordering = ('task_id',)

# ------------------------
# User Tasks
# ------------------------
class UserTasksAdmin(admin.ModelAdmin):
    list_display = ('user_tasks_id', 'user_id', 'task_id', 'assigned_by', 'created_at', 'deadline')
    search_fields = ('user_id__email', 'task_id__title', 'assigned_by__email')
    ordering = ('user_tasks_id',)

# ------------------------
# Task Status
# ------------------------
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ('task_status_id', 'user_task', 'old_status', 'new_status', 'change_date')
    search_fields = ('user_task__task_id__title',)
    ordering = ('task_status_id',)

# ------------------------
# User Grades
# ------------------------
class UserGradeAdmin(admin.ModelAdmin):
    list_display = ('grade_id', 'reviewer', 'reviewed', 'user_task', 'rating', 'created_at')
    search_fields = ('reviewer__email', 'reviewed__email', 'user_task__task_id__title')
    ordering = ('grade_id',)

# ------------------------
# Task Types
# ------------------------
class TaskTypesAdmin(admin.ModelAdmin):
    list_display = ('task_type_id', 'task_type')
    search_fields = ('task_type',)
    ordering = ('task_type_id',)

# ------------------------
# Task Type Text
# ------------------------
class TaskTypeTextAdmin(admin.ModelAdmin):
    list_display = ('task_text_id', 'task', 'content')
    search_fields = ('task__title', 'content')
    ordering = ('task_text_id',)

# ------------------------
# Task Type Quiz
# ------------------------
class TaskTypeQuizAdmin(admin.ModelAdmin):
    list_display = ('task_quiz_id', 'task')
    search_fields = ('task__title',)
    ordering = ('task_quiz_id',)

# ------------------------
# Quizzes
# ------------------------
class QuizzesAdmin(admin.ModelAdmin):
    list_display = ('quiz_id', 'task')
    search_fields = ('task__title',)
    ordering = ('quiz_id',)

# ------------------------
# Quiz Questions
# ------------------------
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_id', 'quiz', 'question')
    search_fields = ('quiz__task__title', 'question')
    ordering = ('question_id',)

# ------------------------
# Quiz Answers
# ------------------------
class QuizAnswersAdmin(admin.ModelAdmin):
    list_display = ('answer_id', 'question', 'answer', 'correct')
    search_fields = ('question__question', 'answer')
    ordering = ('answer_id',)

# ------------------------
# Rejestracja modeli w admin
# ------------------------
admin.site.register(Badges, BadgesAdmin)
admin.site.register(User_badges, UserBadgesAdmin)
admin.site.register(Competency_paths, CompetencyPathsAdmin)
admin.site.register(Reports, ReportsAdmin)
admin.site.register(User_paths, UserPathsAdmin)
admin.site.register(Tasks, TasksAdmin)
admin.site.register(User_tasks, UserTasksAdmin)
admin.site.register(Task_status, TaskStatusAdmin)
admin.site.register(User_grade, UserGradeAdmin)
admin.site.register(Task_types, TaskTypesAdmin)
admin.site.register(Task_type_text, TaskTypeTextAdmin)
admin.site.register(Task_type_quiz, TaskTypeQuizAdmin)
admin.site.register(Quizzes, QuizzesAdmin)
admin.site.register(Quiz_question, QuizQuestionAdmin)
admin.site.register(Quiz_answers, QuizAnswersAdmin)
