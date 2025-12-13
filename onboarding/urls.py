from django.urls import path
from .views import (
    user_tasks_list,
    user_competency_paths_with_tasks,
    mentor_task_management,
    mentor_assign_task,
    mentor_create_task,
    mentor_edit_task,
    mentor_delete_user_task,
    mentor_assign_path,
    mentor_delete_user_path,
    mentor_create_path,
    mentor_change_user_task_status,
)

app_name = "onboarding"

urlpatterns = [
    path('onboarding/tasks/', user_tasks_list, name='user_tasks_list'),
    path('onboarding/paths/', user_competency_paths_with_tasks, name='user_competency_paths_with_tasks'),
    # Mentor routes
    path('mentor/tasks/', mentor_task_management, name='mentor_task_management'),
    path('mentor/tasks/<int:student_id>/', mentor_task_management, name='mentor_task_management'),
    path('mentor/assign-task/<int:student_id>/', mentor_assign_task, name='mentor_assign_task'),
    path('mentor/create-task/', mentor_create_task, name='mentor_create_task'),
    path('mentor/edit-task/<int:task_id>/', mentor_edit_task, name='mentor_edit_task'),
    path('mentor/delete-user-task/<int:user_task_id>/', mentor_delete_user_task, name='mentor_delete_user_task'),
    path('mentor/change-user-task-status/<int:user_task_id>/', mentor_change_user_task_status,
         name='mentor_change_user_task_status'),
    path('mentor/assign-path/<int:student_id>/', mentor_assign_path, name='mentor_assign_path'),
    path('mentor/delete-user-path/<int:user_path_id>/', mentor_delete_user_path, name='mentor_delete_user_path'),
    path('mentor/create-path/', mentor_create_path, name='mentor_create_path'),
]
