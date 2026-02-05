from django import forms
from django.db import models
from .models import Tasks, User_tasks, Competency_paths, User_paths


class TaskForm(forms.ModelForm):
    class Meta:
        model = Tasks
        fields = ['path', 'task_type', 'title', 'description', 'path_order', 'public', 'need_verification']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Opis zadania...'}),
            'title': forms.TextInput(attrs={'placeholder': 'Tytuł zadania...'}),
        }


class UserTaskForm(forms.ModelForm):
    class Meta:
        model = User_tasks
        fields = ['task_id', 'deadline']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'task_id': forms.Select(attrs={'style': 'width: 100%;'}),
        }
        labels = {
            'task_id': 'Zadanie',
            'deadline': 'Termin wykonania',
        }

    def __init__(self, *args, **kwargs):
        task_search = kwargs.pop('task_search', None)
        super().__init__(*args, **kwargs)

        # Filtrowanie zadań na podstawie wyszukiwania
        queryset = Tasks.objects.select_related('path', 'task_type')
        if task_search:
            queryset = queryset.filter(
                models.Q(title__icontains=task_search) |
                models.Q(description__icontains=task_search) |
                models.Q(path__name__icontains=task_search)
            )

        self.fields['task_id'].queryset = queryset
        self.fields['task_id'].label_from_instance = lambda \
            obj: f"{obj.title} [{obj.path.name if obj.path else 'Brak ścieżki'}]"


class UserPathForm(forms.ModelForm):
    class Meta:
        model = User_paths
        fields = ['path']
        widgets = {
            'path': forms.Select(attrs={'style': 'width: 100%;'}),
        }
        labels = {
            'path': 'Ścieżka kompetencji',
        }

    def __init__(self, *args, **kwargs):
        path_search = kwargs.pop('path_search', None)
        super().__init__(*args, **kwargs)

        # Filtrowanie ścieżek na podstawie wyszukiwania
        queryset = Competency_paths.objects.all()
        if path_search:
            queryset = queryset.filter(
                models.Q(name__icontains=path_search) |
                models.Q(description__icontains=path_search)
            )

        self.fields['path'].queryset = queryset
        self.fields['path'].label_from_instance = lambda obj: f"{obj.name} - {obj.description[:50]}..."


class CompetencyPathForm(forms.ModelForm):
    class Meta:
        model = Competency_paths
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Opis ścieżki kompetencji...'}),
            'name': forms.TextInput(attrs={'placeholder': 'Nazwa ścieżki kompetencji...'}),
        }
        labels = {
            'name': 'Nazwa',
            'description': 'Opis',
        }
