from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import User_tasks, User_paths, Tasks, Task_status, Competency_paths
from .forms import TaskForm, UserTaskForm, UserPathForm

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

    # Pobranie zadań wybranego studenta
    student_tasks = User_tasks.objects.filter(
        user_id=selected_student
    ).select_related('task_id', 'task_id__path', 'assigned_by').prefetch_related('statuses')

    # Przygotowanie danych o statusach zadań
    tasks_with_status = []
    for utask in student_tasks:
        latest_status = utask.statuses.order_by('-change_date').first()
        tasks_with_status.append({
            'user_task': utask,
            'current_status': latest_status.new_status if latest_status else Task_status.Status.DO_ZROBIENIA
        })

    # Paginacja
    page_number = request.GET.get('page', 1)
    paginator = Paginator(tasks_with_status, 10)  # 10 zadań na stronę
    page_obj = paginator.get_page(page_number)

    # Pobranie ścieżek studenta
    student_paths = User_paths.objects.filter(
        user=selected_student
    ).select_related('path', 'assigned_by')

    return render(request, 'onboarding/mentor_task_management.html', {
        'students': students,
        'selected_student': selected_student,
        'page_obj': page_obj,
        'student_paths': student_paths,
    })

@login_required
def mentor_assign_task(request, student_id):
    mentor = request.user

    # Sprawdzenie, czy użytkownik jest mentorem
    if not mentor.is_mentor:
        return render(request, "exceptions/no_students.html")

    student = get_object_or_404(mentor.mentees, id=student_id)

    if request.method == 'POST':
        form = UserTaskForm(request.POST)
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
        form = UserTaskForm()

    return render(request, 'onboarding/mentor_assign_task.html', {
        'form': form,
        'student': student,
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

    if request.method == 'POST':
        form = UserPathForm(request.POST)
        if form.is_valid():
            user_path = form.save(commit=False)
            user_path.user = student
            user_path.assigned_by = mentor
            user_path.save()
            return redirect('onboarding:mentor_task_management', student_id=student.id)
    else:
        form = UserPathForm()

    return render(request, 'onboarding/mentor_assign_path.html', {
        'form': form,
        'student': student,
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