from django.urls import path
from .views import user_tasks_list, user_competency_paths_with_tasks, user_task_detail

app_name = "onboarding"

urlpatterns = [
    path('onboarding/tasks/', user_tasks_list, name='user_tasks_list'),
    path('onboarding/paths/', user_competency_paths_with_tasks, name='user_competency_paths_with_tasks'),
    path("task/<int:user_task_id>/", user_task_detail, name="user_task_detail"),
]
