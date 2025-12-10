from django.shortcuts import render
from .models import User_tasks,User_paths

def user_tasks_list(request):
    # Pobiera tylko zadania zalogowanego użytkownika
    tasks = User_tasks.objects.filter(user_id=request.user) if request.user.is_authenticated else []
    return render(request, 'onboarding/user_tasks_list.html', {'tasks': tasks})

def user_paths_list(request):
    # Pobiera tylko ścieżki zalogowanego użytkownika
    paths = request.user.user_paths.all() if request.user.is_authenticated else []
    return render(request, 'onboarding/user_paths_list.html', {'paths': paths})

def user_competency_paths_with_tasks(request):
    if not request.user.is_authenticated:
        paths_with_tasks = []
    else:
        # Pobierz wszystkie ścieżki przypisane do użytkownika
        user_paths = request.user.user_paths.all().select_related('path').order_by('path_id')
        
        # Przygotuj listę słowników: każda ścieżka + zadania w niej
        paths_with_tasks = []
        for up in user_paths:
            tasks = up.path.competency_path.all()  # Tasks związane z tą ścieżką
            paths_with_tasks.append({
                'user_path': up,
                'tasks': tasks
            })

    return render(request, 'onboarding/user_competency_paths_with_tasks.html', {'paths_with_tasks': paths_with_tasks})