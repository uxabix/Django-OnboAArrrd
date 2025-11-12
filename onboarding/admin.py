from django.contrib import admin
from .models import (
    Badges,
    User_badges,
    Competency_paths,
    Reports,
    User_paths,
    Tasks,
    Task_status,
    Mentor_grade
)

class BadgesAdmin(admin.ModelAdmin):
    list_display = ('badge_id', 'name', 'points', 'description')
    search_fields = ('name',)
    ordering = ('badge_id',)

class UserBadgesAdmin(admin.ModelAdmin):
    list_display = ('user_badge_id', 'user', 'badge')
    search_fields = ('user__email', 'badge__name')
    ordering = ('user_badge_id',)

class CompetencyPathsAdmin(admin.ModelAdmin):
    list_display = ('path_id', 'name', 'mentor', 'created_at')
    search_fields = ('name', 'mentor__email')
    ordering = ('path_id',)

class ReportsAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'user', 'generated_by', 'created_at', 'file_path')
    search_fields = ('user__email', 'generated_by__email')
    ordering = ('report_id',)

class UserPathsAdmin(admin.ModelAdmin):
    list_display = ('user_path_id', 'user', 'path', 'assigned_by', 'assigned_at')
    search_fields = ('user__email', 'path__name', 'assigned_by__email')
    ordering = ('user_path_id',)

class TasksAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'title', 'path', 'mentor', 'assigned_to', 'created_at', 'deadline')
    search_fields = ('title', 'path__name', 'mentor__email', 'assigned_to__email')
    ordering = ('task_id',)

class TaskStatusAdmin(admin.ModelAdmin):
    list_display = ('status_id', 'task', 'changed_by', 'old_status', 'new_status', 'change_date')
    search_fields = ('task__title', 'changed_by__email')
    ordering = ('status_id',)

class MentorGradeAdmin(admin.ModelAdmin):
    list_display = ('grade_id', 'mentor', 'reviewer', 'task')
    search_fields = ('mentor__email', 'reviewer__email', 'task__title')
    ordering = ('grade_id',)

admin.site.register(Badges, BadgesAdmin)
admin.site.register(User_badges, UserBadgesAdmin)
admin.site.register(Competency_paths, CompetencyPathsAdmin)
admin.site.register(Reports, ReportsAdmin)
admin.site.register(User_paths, UserPathsAdmin)
admin.site.register(Tasks, TasksAdmin)
admin.site.register(Task_status, TaskStatusAdmin)
admin.site.register(Mentor_grade, MentorGradeAdmin)
