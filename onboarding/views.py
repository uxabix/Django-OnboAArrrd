from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from .models import User_tasks, User_paths, Tasks, Task_status, Competency_paths
from .forms import TaskForm, UserTaskForm, UserPathForm, CompetencyPathForm

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

@login_required
def mentor_task_management(request, student_id=None):
    mentor = request.user

    # Sprawdzenie, czy użytkownik jest mentorem
    if not mentor.is_mentor:
        return render(request, "exceptions/no_students.html")

    # Pobranie wszystkich studentów mentora
    students = mentor.mentees.all()

    if not students.exists():
        return render(request, "exceptions/no_students.html")

    # Jeśli nie wybrano studenta, wybierz pierwszego
    if student_id is None:
        selected_student = students.first()
    else:
        selected_student = students.filter(id=student_id).first()

    if selected_student is None:
        return render(request, "exceptions/no_student_found.html")

    # Parametry wyszukiwania i filtrowania dla zadań
    task_search = request.GET.get('task_search', '').strip()
    task_sort = request.GET.get('task_sort', '-created_at')
    task_status_filter = request.GET.get('task_status', '')

    # Pobranie zadań wybranego studenta
    student_tasks = User_tasks.objects.filter(
        user_id=selected_student
    ).select_related('task_id', 'task_id__path', 'assigned_by').prefetch_related('statuses')

    # Filtrowanie zadań po wyszukiwaniu
    if task_search:
        student_tasks = student_tasks.filter(
            models.Q(task_id__title__icontains=task_search) |
            models.Q(task_id__description__icontains=task_search) |
            models.Q(task_id__path__name__icontains=task_search)
        )

    # Przygotowanie danych o statusach zadań
    tasks_with_status = []
    for utask in student_tasks:
        latest_status = utask.statuses.order_by('-change_date').first()
        current_status = latest_status.new_status if latest_status else Task_status.Status.DO_ZROBIENIA

        # Filtrowanie po statusie
        if task_status_filter and current_status != task_status_filter:
            continue

        tasks_with_status.append({
            'user_task': utask,
            'current_status': current_status
        })

    # Sortowanie zadań
    if task_sort == 'title':
        tasks_with_status.sort(key=lambda x: x['user_task'].task_id.title)
    elif task_sort == '-title':
        tasks_with_status.sort(key=lambda x: x['user_task'].task_id.title, reverse=True)
    elif task_sort == 'deadline':
        tasks_with_status.sort(key=lambda x: x['user_task'].deadline)
    elif task_sort == '-deadline':
        tasks_with_status.sort(key=lambda x: x['user_task'].deadline, reverse=True)
    elif task_sort == 'created_at':
        tasks_with_status.sort(key=lambda x: x['user_task'].created_at)
    else:  # -created_at (domyślne)
        tasks_with_status.sort(key=lambda x: x['user_task'].created_at, reverse=True)

    # Paginacja dla zadań
    tasks_page_number = request.GET.get('tasks_page', 1)
    tasks_paginator = Paginator(tasks_with_status, 10)
    tasks_page_obj = tasks_paginator.get_page(tasks_page_number)

    # Parametry wyszukiwania i filtrowania dla ścieżek
    path_search = request.GET.get('path_search', '').strip()
    path_sort = request.GET.get('path_sort', '-assigned_at')

    # Pobranie ścieżek studenta
    student_paths = User_paths.objects.filter(
        user=selected_student
    ).select_related('path', 'assigned_by')

    # Filtrowanie ścieżek po wyszukiwaniu
    if path_search:
        student_paths = student_paths.filter(
            models.Q(path__name__icontains=path_search) |
            models.Q(path__description__icontains=path_search)
        )

    # Sortowanie ścieżek
    if path_sort == 'name':
        student_paths = student_paths.order_by('path__name')
    elif path_sort == '-name':
        student_paths = student_paths.order_by('-path__name')
    elif path_sort == 'assigned_at':
        student_paths = student_paths.order_by('assigned_at')
    else:  # -assigned_at (domyślne)
        student_paths = student_paths.order_by('-assigned_at')

    # Paginacja dla ścieżek
    paths_page_number = request.GET.get('paths_page', 1)
    paths_paginator = Paginator(student_paths, 10)
    paths_page_obj = paths_paginator.get_page(paths_page_number)

    return render(request, 'onboarding/mentor_task_management.html', {
        'students': students,
        'selected_student': selected_student,
        'tasks_page_obj': tasks_page_obj,
        'paths_page_obj': paths_page_obj,
        'task_search': task_search,
        'task_sort': task_sort,
        'task_status_filter': task_status_filter,
        'path_search': path_search,
        'path_sort': path_sort,
        'task_statuses': Task_status.Status.choices,
    })

@login_required
def mentor_assign_task(request, student_id):
    mentor = request.user

    # Sprawdzenie, czy użytkownik jest mentorem
    if not mentor.is_mentor:
        return render(request, "exceptions/no_students.html")

    student = get_object_or_404(mentor.mentees, id=student_id)
    task_search = request.GET.get('task_search', '')

    if request.method == 'POST':
        form = UserTaskForm(request.POST, task_search=task_search)
        if form.is_valid():
            user_task = form.save(commit=False)
            user_task.user_id = student
            user_task.assigned_by = mentor
            user_task.save()

            # Создание начального статуса задачи
            Task_status.objects.create(
                user_task=user_task,
                new_status=Task_status.Status.DO_ZROBIENIA
            )

            return redirect('onboarding:mentor_task_management', student_id=student.id)
    else:
        form = UserTaskForm(task_search=task_search)

    return render(request, 'onboarding/mentor_assign_task.html', {
        'form': form,
        'student': student,
        'task_search': task_search,
    })

@login_required
def mentor_create_task(request):
    mentor = request.user

    # Sprawdzenie, czy użytkownik jest mentorem
    if not mentor.is_mentor:
        return render(request, "exceptions/no_students.html")

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            return redirect('onboarding:mentor_task_management')
    else:
        form = TaskForm()

    return render(request, 'onboarding/mentor_create_task.html', {
        'form': form,
    })

@login_required
def mentor_edit_task(request, task_id):
    mentor = request.user

    # Sprawdzenie, czy użytkownik jest mentorem
    if not mentor.is_mentor:
        return render(request, "exceptions/no_students.html")

    task = get_object_or_404(Tasks, task_id=task_id)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('onboarding:mentor_task_management')
    else:
        form = TaskForm(instance=task)

    return render(request, 'onboarding/mentor_edit_task.html', {
        'form': form,
        'task': task,
    })

@login_required
def mentor_delete_user_task(request, user_task_id):
    mentor = request.user

    # Sprawdzenie, czy użytkownik jest mentorem
    if not mentor.is_mentor:
        return render(request, "exceptions/no_students.html")

    user_task = get_object_or_404(User_tasks, user_tasks_id=user_task_id)
    student_id = user_task.user_id.id

    if request.method == 'POST':
        user_task.delete()
        return redirect('onboarding:mentor_task_management', student_id=student_id)

    return render(request, 'onboarding/mentor_delete_user_task.html', {
        'user_task': user_task,
    })

@login_required
def mentor_assign_path(request, student_id):
    mentor = request.user

    # Sprawdzenie, czy użytkownik jest mentorem
    if not mentor.is_mentor:
        return render(request, "exceptions/no_students.html")

    student = get_object_or_404(mentor.mentees, id=student_id)
    path_search = request.GET.get('path_search', '')

    if request.method == 'POST':
        form = UserPathForm(request.POST, path_search=path_search)
        if form.is_valid():
            user_path = form.save(commit=False)
            user_path.user = student
            user_path.assigned_by = mentor
            user_path.save()
            return redirect('onboarding:mentor_task_management', student_id=student.id)
    else:
        form = UserPathForm(path_search=path_search)

    return render(request, 'onboarding/mentor_assign_path.html', {
        'form': form,
        'student': student,
        'path_search': path_search,
    })

@login_required
def mentor_delete_user_path(request, user_path_id):
    mentor = request.user

    # Sprawdzenie, czy użytkownik jest mentorem
    if not mentor.is_mentor:
        return render(request, "exceptions/no_students.html")

    user_path = get_object_or_404(User_paths, user_path_id=user_path_id)
    student_id = user_path.user.id

    if request.method == 'POST':
        user_path.delete()
        return redirect('onboarding:mentor_task_management', student_id=student_id)

    return render(request, 'onboarding/mentor_delete_user_path.html', {
        'user_path': user_path,
    })

@login_required
def mentor_create_path(request):
    mentor = request.user

    # Sprawdzenie, czy użytkownik jest mentorem
    if not mentor.is_mentor:
        return render(request, "exceptions/no_students.html")

    if request.method == 'POST':
        form = CompetencyPathForm(request.POST)
        if form.is_valid():
            competency_path = form.save()
            return redirect('onboarding:mentor_task_management')
    else:
        form = CompetencyPathForm()

    return render(request, 'onboarding/mentor_create_path.html', {
        'form': form,
    })