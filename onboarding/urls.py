from django.urls import path
from .views import user_tasks_list, user_competency_paths_with_tasks

app_name = "onboarding"

urlpatterns = [
    path('onboarding/tasks/', user_tasks_list, name='user_tasks_list'),
    path('onboarding/paths/', user_competency_paths_with_tasks, name='user_competency_paths_with_tasks'),
]
