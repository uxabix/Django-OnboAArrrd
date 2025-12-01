from django.shortcuts import render
from .models import User_tasks

def user_tasks_list(request):
    # Pobiera tylko zadania zalogowanego użytkownika
    tasks = User_tasks.objects.filter(user_id=request.user) if request.user.is_authenticated else []
    return render(request, 'onboarding/user_tasks_list.html', {'tasks': tasks})
