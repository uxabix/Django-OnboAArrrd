from django import forms
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
        }
        labels = {
            'task_id': 'Zadanie',
            'deadline': 'Termin wykonania',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Wyświetlanie zadań z dodatkowymi informacjami
        self.fields['task_id'].queryset = Tasks.objects.select_related('path', 'task_type')
        self.fields['task_id'].label_from_instance = lambda obj: f"{obj.title} [{obj.path.name if obj.path else 'Brak ścieżki'}]"

class UserPathForm(forms.ModelForm):
    class Meta:
        model = User_paths
        fields = ['path']
        labels = {
            'path': 'Ścieżka kompetencji',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['path'].queryset = Competency_paths.objects.all()
        self.fields['path'].label_from_instance = lambda obj: f"{obj.name} - {obj.description[:50]}..."
