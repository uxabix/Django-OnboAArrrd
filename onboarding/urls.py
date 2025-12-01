from django.urls import path
from .views import user_tasks_list

app_name = "onboarding"

urlpatterns = [
    path('onboarding/', user_tasks_list, name='user_tasks_list'),
]
