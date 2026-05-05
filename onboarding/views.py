import calendar
import json
from datetime import timedelta
from collections import defaultdict
from django.utils.dateparse import parse_date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CompetencyPathForm, TaskForm, UserPathForm, UserTaskForm
from .models import (
    Competency_paths,
    Task_status,
    Task_types,
    Tasks,
    User_paths,
    User_tasks,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DEADLINE_FILTERS = {
    'all': 'Wszystkie',
    'active': 'Aktywne',
    'approaching': 'Zbliżający się termin',
    'overdue': 'Przeterminowane',
    'completed': 'Ukończone / oddane',
}

PATH_SORT_OPTIONS = {
    '-assigned_at': 'Najnowsze przypisanie',
    'assigned_at': 'Najstarsze przypisanie',
    'name': 'Nazwa A-Z',
    '-name': 'Nazwa Z-A',
    '-tasks_total': 'Najwięcej zadań',
    '-tasks_open': 'Najwięcej aktywnych',
}

TASK_SORT_OPTIONS = {
    'path_order': 'Kolejność w ścieżce',
    'title': 'Tytuł A-Z',
    '-title': 'Tytuł Z-A',
    'deadline': 'Deadline rosnąco',
    '-deadline': 'Deadline malejąco',
    'status': 'Status A-Z',
}


def _build_user_tasks_with_state(user):
    """Pobiera wszystkie zadania użytkownika i wzbogaca je o stan terminu.
    Zwraca listę dictów oraz statystyki."""
    qs = (
        User_tasks.objects.filter(user_id=user)
        .select_related('task_id', 'task_id__path', 'assigned_by')
        .prefetch_related('statuses')
        .order_by('deadline')
    )

    enriched = []
    stats = {'total': 0, 'active': 0, 'approaching': 0, 'overdue': 0, 'completed': 0}
    today = timezone.now().date()
    reminders = []

    for ut in qs:
        state = ut.deadline_state
        item = {
            'user_task': ut,
            'state': state,
            'current_status': ut.current_status,
            'days_until_deadline': ut.days_until_deadline,
            'submission_date': ut.submission_date,
        }
        enriched.append(item)
        stats['total'] += 1
        if state in ('on_time', 'late'):
            stats['completed'] += 1
        elif state == 'overdue':
            stats['overdue'] += 1
        elif state == 'approaching':
            stats['approaching'] += 1
            stats['active'] += 1
            reminders.append(item)
        else:
            stats['active'] += 1

    return enriched, stats, reminders, today


# ---------------------------------------------------------------------------
# Student views
# ---------------------------------------------------------------------------


@login_required
def user_tasks_list(request):
    enriched, stats, reminders, today = _build_user_tasks_with_state(request.user)

    filter_param = request.GET.get('filter', 'active')
    if filter_param not in DEADLINE_FILTERS:
        filter_param = 'active'

    if filter_param == 'active':
        filtered = [t for t in enriched if t['state'] in ('on_track', 'approaching')]
    elif filter_param == 'approaching':
        filtered = [t for t in enriched if t['state'] == 'approaching']
    elif filter_param == 'overdue':
        filtered = [t for t in enriched if t['state'] == 'overdue']
    elif filter_param == 'completed':
        filtered = [t for t in enriched if t['state'] in ('on_time', 'late')]
    else:
        filtered = enriched

    page_number = request.GET.get('page', 1)
    paginator = Paginator(filtered, 15)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'onboarding/user_tasks_list.html',
        {
            'page_obj': page_obj,
            'stats': stats,
            'reminders': reminders,
            'filter': filter_param,
            'filter_options': DEADLINE_FILTERS,
            'today': today,
        },
    )


@login_required
def user_tasks_calendar(request, year=None, month=None):
    today = timezone.now().date()
    try:
        year = int(year) if year else today.year
        month = int(month) if month else today.month
    except (TypeError, ValueError):
        year, month = today.year, today.month

    if not (1 <= month <= 12):
        year, month = today.year, today.month

    enriched, stats, reminders, _ = _build_user_tasks_with_state(request.user)

    # Dla mentorów: dodatkowo pokaż deadline'y zadań ich podopiecznych.
    mentee_enriched = []
    if request.user.is_mentor:
        mentee_tasks = (
            User_tasks.objects.filter(user_id__mentor=request.user)
            .select_related('user_id', 'task_id', 'task_id__path', 'assigned_by')
            .prefetch_related('statuses')
            .order_by('deadline')
        )
        for ut in mentee_tasks:
            mentee_enriched.append({
                'user_task': ut,
                'state': ut.deadline_state,
                'current_status': ut.current_status,
                'days_until_deadline': ut.days_until_deadline,
                'submission_date': ut.submission_date,
                'is_mentee_task': True,
                'student_name': f"{ut.user_id.first_name} {ut.user_id.last_name}".strip() or ut.user_id.email,
            })

    for item in enriched:
        item['is_mentee_task'] = False

    # Mapa: data -> lista zadań
    tasks_by_date = {}
    for item in enriched + mentee_enriched:
        d = item['user_task'].deadline
        tasks_by_date.setdefault(d, []).append(item)

    cal = calendar.Calendar(firstweekday=0)  # poniedziałek
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        week_data = []
        for day in week:
            day_tasks = tasks_by_date.get(day, [])
            week_data.append({
                'date': day,
                'in_month': day.month == month,
                'is_today': day == today,
                'tasks': day_tasks,
                'has_overdue': any(t['state'] == 'overdue' for t in day_tasks),
                'has_approaching': any(t['state'] == 'approaching' for t in day_tasks),
                'has_completed': any(t['state'] in ('on_time', 'late') for t in day_tasks),
            })
        weeks.append(week_data)

    # Nawigacja po miesiącach
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    month_names_pl = [
        '', 'Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec',
        'Lipiec', 'Sierpień', 'Wrzesień', 'Październik', 'Listopad', 'Grudzień'
    ]
    weekday_names_pl = ['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Ndz']

    return render(
        request,
        'onboarding/user_tasks_calendar.html',
        {
            'weeks': weeks,
            'year': year,
            'month': month,
            'month_name': month_names_pl[month],
            'weekday_names': weekday_names_pl,
            'prev_year': prev_year,
            'prev_month': prev_month,
            'next_year': next_year,
            'next_month': next_month,
            'today_year': today.year,
            'today_month': today.month,
            'stats': stats,
            'reminders': reminders,
            'is_mentor': request.user.is_mentor,
        },
    )


@login_required
def user_submit_task(request, user_task_id):
    """Pozwala studentowi oznaczyć swoje zadanie jako wysłane do weryfikacji."""
    user_task = get_object_or_404(User_tasks, pk=user_task_id, user_id=request.user)

    if request.method != 'POST':
        return redirect('onboarding:user_task_detail', user_task_id=user_task.user_tasks_id)

    if user_task.is_submitted:
        messages.info(request, "To zadanie zostało już wcześniej oddane.")
        return redirect('onboarding:user_task_detail', user_task_id=user_task.user_tasks_id)

    Task_status.objects.create(
        user_task=user_task,
        old_status=user_task.current_status,
        new_status=Task_status.Status.DO_WERYFIKACJI,
    )

    if user_task.deadline < timezone.now().date():
        messages.warning(
            request,
            "Zadanie zostało wysłane do weryfikacji, ale po terminie (deadline minął).",
        )
    else:
        messages.success(request, "Zadanie zostało wysłane do weryfikacji w terminie.")

    return redirect('onboarding:user_task_detail', user_task_id=user_task.user_tasks_id)


def user_paths_list(request):
    # Pobiera tylko ścieżki zalogowanego użytkownika
    paths = request.user.user_paths.all() if request.user.is_authenticated else []
    return render(request, 'onboarding/user_paths_list.html', {'paths': paths})


@login_required
def user_competency_paths_with_tasks(request):
    path_sort = request.GET.get('path_sort', '-assigned_at')
    task_sort = request.GET.get('task_sort', 'path_order')
    show_completed = request.GET.get('show_completed', '0') == '1'

    if path_sort not in PATH_SORT_OPTIONS:
        path_sort = '-assigned_at'
    if task_sort not in TASK_SORT_OPTIONS:
        task_sort = 'path_order'

    user_paths = (
        request.user.user_paths.all()
        .select_related('path', 'assigned_by')
        .prefetch_related('path__competency_path')
    )

    # Zadania przypisane konkretnemu użytkownikowi (z historią statusów).
    user_tasks = (
        User_tasks.objects.filter(user_id=request.user)
        .select_related('task_id', 'task_id__path')
        .prefetch_related('statuses')
    )

    task_map = defaultdict(list)
    for user_task in user_tasks:
        if user_task.task_id and user_task.task_id.path_id:
            task_map[user_task.task_id.path_id].append(user_task)

    paths_with_tasks = []
    for up in user_paths:
        path_tasks = list(up.path.competency_path.all().select_related('task_type'))
        user_tasks_by_task_id = {
            ut.task_id_id: ut
            for ut in sorted(task_map.get(up.path_id, []), key=lambda item: item.created_at, reverse=True)
        }

        tasks = []
        for task in path_tasks:
            user_task = user_tasks_by_task_id.get(task.task_id)
            current_status = user_task.current_status if user_task else Task_status.Status.DO_ZROBIENIA
            deadline_state = user_task.deadline_state if user_task else 'on_track'
            is_completed = bool(user_task and user_task.is_completed)

            tasks.append({
                'task': task,
                'user_task': user_task,
                'current_status': current_status,
                'deadline_state': deadline_state,
                'is_completed': is_completed,
                'deadline': user_task.deadline if user_task else None,
                'path_order': task.path_order if task.path_order is not None else 99999,
            })

        if task_sort == 'title':
            tasks.sort(key=lambda x: (x['task'].title or '').lower())
        elif task_sort == '-title':
            tasks.sort(key=lambda x: (x['task'].title or '').lower(), reverse=True)
        elif task_sort == 'deadline':
            tasks.sort(key=lambda x: (x['deadline'] is None, x['deadline'] or timezone.now().date()))
        elif task_sort == '-deadline':
            tasks.sort(key=lambda x: (x['deadline'] is None, x['deadline'] or timezone.now().date()), reverse=True)
        elif task_sort == 'status':
            tasks.sort(key=lambda x: (x['current_status'] or '').lower())
        else:
            tasks.sort(key=lambda x: (x['path_order'], (x['task'].title or '').lower()))

        visible_tasks = tasks if show_completed else [t for t in tasks if not t['is_completed']]

        paths_with_tasks.append({
            'user_path': up,
            'tasks': visible_tasks,
            'total_tasks_count': len(tasks),
            'visible_tasks_count': len(visible_tasks),
            'completed_tasks_count': len([t for t in tasks if t['is_completed']]),
            'open_tasks_count': len([t for t in tasks if not t['is_completed']]),
        })

    if path_sort == 'name':
        paths_with_tasks.sort(key=lambda x: (x['user_path'].path.name or '').lower())
    elif path_sort == '-name':
        paths_with_tasks.sort(key=lambda x: (x['user_path'].path.name or '').lower(), reverse=True)
    elif path_sort == 'assigned_at':
        paths_with_tasks.sort(key=lambda x: x['user_path'].assigned_at)
    elif path_sort == '-tasks_total':
        paths_with_tasks.sort(key=lambda x: x['total_tasks_count'], reverse=True)
    elif path_sort == '-tasks_open':
        paths_with_tasks.sort(key=lambda x: x['open_tasks_count'], reverse=True)
    else:
        paths_with_tasks.sort(key=lambda x: x['user_path'].assigned_at, reverse=True)

    return render(
        request,
        'onboarding/user_competency_paths_with_tasks.html',
        {
            'paths_with_tasks': paths_with_tasks,
            'path_sort': path_sort,
            'task_sort': task_sort,
            'show_completed': show_completed,
            'path_sort_options': PATH_SORT_OPTIONS,
            'task_sort_options': TASK_SORT_OPTIONS,
        }
    )

@login_required
def user_task_detail(request, user_task_id):
    user_task = get_object_or_404(
        User_tasks.objects.select_related('task_id', 'task_id__path', 'assigned_by').prefetch_related('statuses'),
        pk=user_task_id,
        user_id=request.user,
    )

    statuses = user_task.statuses.order_by("-change_date")

    return render(request, "onboarding/user_task_detail.html", {
        "user_task": user_task,
        "statuses": statuses,
        "deadline_state": user_task.deadline_state,
        "current_status": user_task.current_status,
        "days_until_deadline": user_task.days_until_deadline,
    })

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
    deadline_filter = request.GET.get('deadline_state', '')

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
    deadline_summary = {'on_time': 0, 'late': 0, 'overdue': 0, 'approaching': 0, 'on_track': 0}
    for utask in student_tasks:
        current_status = utask.current_status
        deadline_state = utask.deadline_state
        deadline_summary[deadline_state] = deadline_summary.get(deadline_state, 0) + 1

        if task_status_filter and current_status != task_status_filter:
            continue

        if deadline_filter and deadline_state != deadline_filter:
            continue

        tasks_with_status.append({
            'user_task': utask,
            'current_status': current_status,
            'deadline_state': deadline_state,
            'days_until_deadline': utask.days_until_deadline,
            'submission_date': utask.submission_date,
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

    deadline_filter_options = [
        ('', 'Wszystkie terminy'),
        ('on_track', 'W trakcie (z czasem)'),
        ('approaching', 'Zbliżający się termin'),
        ('overdue', 'Przeterminowane (brak oddania)'),
        ('on_time', 'Oddane w terminie'),
        ('late', 'Oddane po terminie'),
    ]

    return render(request, 'onboarding/mentor_task_management.html', {
        'students': students,
        'selected_student': selected_student,
        'tasks_page_obj': tasks_page_obj,
        'paths_page_obj': paths_page_obj,
        'task_search': task_search,
        'task_sort': task_sort,
        'task_status_filter': task_status_filter,
        'deadline_filter': deadline_filter,
        'deadline_filter_options': deadline_filter_options,
        'deadline_summary': deadline_summary,
        'path_search': path_search,
        'path_sort': path_sort,
        'task_statuses': Task_status.Status.choices,
        'today': timezone.now().date(),
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

            # Create initial task status
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
        form = UserPathForm(request.POST)
        assignment_data_raw = request.POST.get('assignment_data', '[]')
        if form.is_valid():
            try:
                assignment_data = json.loads(assignment_data_raw)
            except json.JSONDecodeError:
                form.add_error(None, 'Nieprawidłowe dane zadań do przypisania.')
                assignment_data = []

            path = form.cleaned_data['path']
            path_task_ids = set(Tasks.objects.filter(path=path).values_list('task_id', flat=True))

            validated_assignments = []
            for item in assignment_data:
                try:
                    task_id = int(item.get('task_id'))
                except (TypeError, ValueError):
                    continue
                deadline_raw = item.get('deadline')
                order = item.get('order')
                deadline = parse_date(deadline_raw) if deadline_raw else None

                if task_id not in path_task_ids:
                    continue
                if deadline is None:
                    form.add_error(None, 'Każde przypisywane zadanie musi mieć deadline.')
                    break
                validated_assignments.append({
                    'task_id': task_id,
                    'deadline': deadline,
                    'order': order if isinstance(order, int) else 0,
                })

            if not form.non_field_errors():
                with transaction.atomic():
                    user_path = form.save(commit=False)
                    user_path.user = student
                    user_path.assigned_by = mentor
                    user_path.save()

                    for assignment in sorted(validated_assignments, key=lambda x: x['order']):
                        task = Tasks.objects.get(task_id=assignment['task_id'])
                        user_task = User_tasks.objects.create(
                            user_id=student,
                            task_id=task,
                            assigned_by=mentor,
                            deadline=assignment['deadline'],
                        )
                        Task_status.objects.create(
                            user_task=user_task,
                            new_status=Task_status.Status.DO_ZROBIENIA
                        )

                return redirect('onboarding:mentor_task_management', student_id=student.id)
    else:
        form = UserPathForm(path_search=path_search)

    default_deadline = (timezone.now().date() + timedelta(days=7)).isoformat()

    return render(request, 'onboarding/mentor_assign_path.html', {
        'form': form,
        'student': student,
        'path_search': path_search,
        'default_deadline': default_deadline,
    })


@login_required
def mentor_path_tasks_json(request, path_id):
    mentor = request.user
    if not mentor.is_mentor:
        return JsonResponse({'ok': False, 'error': 'Brak uprawnień.'}, status=403)

    tasks = (
        Tasks.objects
        .filter(path_id=path_id)
        .select_related('task_type')
        .order_by('path_order', 'title')
    )
    return JsonResponse({
        'ok': True,
        'tasks': [
            {
                'id': task.task_id,
                'title': task.title or '(bez tytułu)',
                'description': task.description or '',
                'task_type': task.task_type.task_type if task.task_type else 'Brak typu',
                'path_order': task.path_order or 0,
            }
            for task in tasks
        ]
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
def mentor_change_user_task_status(request, user_task_id):
    mentor = request.user

    # Check role
    if not mentor.is_mentor:
        return render(request, "exceptions/no_students.html")

    user_task = get_object_or_404(User_tasks.objects.select_related('user_id', 'assigned_by'),
                                  user_tasks_id=user_task_id)

    # Check if task is assigned by current user
    if user_task.assigned_by_id != mentor.id:
        return render(request, "exceptions/no_students.html")

    if request.method != 'POST':
        # Изменение статуса только POST'ом
        return redirect('onboarding:mentor_task_management', student_id=user_task.user_id.id)

    new_status = request.POST.get('new_status', '').strip()

    # Validate status
    valid_values = {choice[0] for choice in Task_status.Status.choices}
    if new_status not in valid_values:
        return redirect('onboarding:mentor_task_management', student_id=user_task.user_id.id)

    latest = user_task.statuses.order_by('-change_date').first()
    old_status = latest.new_status if latest else None

    # Tworzymy nowy rekord historii statusów (zamiast nadpisywania) — pozwala to
    # zachować historię i poprawnie ocenić terminowość oddania zadania.
    Task_status.objects.create(
        user_task=user_task,
        old_status=old_status,
        new_status=new_status,
    )

    return redirect('onboarding:mentor_task_management', student_id=user_task.user_id.id)


@login_required
def mentor_create_path(request):
    mentor = request.user

    if not mentor.is_mentor:
        return render(request, "exceptions/no_students.html")

    if request.method == 'POST':
        form = CompetencyPathForm(request.POST)
        selected_task_ids_raw = request.POST.get('selected_tasks', '')
        task_ids = [int(task_id) for task_id in selected_task_ids_raw.split(',') if task_id.strip().isdigit()]

        if form.is_valid():
            with transaction.atomic():
                competency_path = form.save()
                for index, task_id in enumerate(task_ids, start=1):
                    Tasks.objects.filter(task_id=task_id).update(
                        path=competency_path,
                        path_order=index,
                    )
            return redirect('onboarding:mentor_task_management')
    else:
        form = CompetencyPathForm()

    task_types = Task_types.objects.order_by('task_type')
    existing_tasks = (
        Tasks.objects
        .select_related('path', 'task_type')
        .order_by('path__name', 'path_order', 'title')
    )

    return render(request, 'onboarding/mentor_create_path.html', {
        'form': form,
        'task_types': task_types,
        'existing_tasks': existing_tasks,
    })


@login_required
def mentor_create_task_inline(request):
    mentor = request.user

    if not mentor.is_mentor:
        return JsonResponse({'ok': False, 'error': 'Brak uprawnień.'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Nieprawidłowa metoda.'}, status=405)

    title = (request.POST.get('title') or '').strip()
    description = (request.POST.get('description') or '').strip()
    task_type_id = request.POST.get('task_type')
    is_public = request.POST.get('public') == 'on'
    need_verification = request.POST.get('need_verification') == 'on'

    if not title:
        return JsonResponse({'ok': False, 'error': 'Tytuł jest wymagany.'}, status=400)

    task_type = None
    if task_type_id:
        task_type = Task_types.objects.filter(task_type_id=task_type_id).first()
        if task_type is None:
            return JsonResponse({'ok': False, 'error': 'Nieprawidłowy typ zadania.'}, status=400)

    task = Tasks.objects.create(
        title=title,
        description=description,
        task_type=task_type,
        public=is_public,
        need_verification=need_verification,
    )

    return JsonResponse({
        'ok': True,
        'task': {
            'id': task.task_id,
            'title': task.title,
            'description': task.description or '',
            'task_type': task.task_type.task_type if task.task_type else 'Brak typu',
            'path_name': 'Brak ścieżki',
            'public': bool(task.public),
            'need_verification': bool(task.need_verification),
        }
    })
