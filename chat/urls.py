from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    # przykładowe ścieżki:
    path("student/", views.chat_student, name="chat_student"),

    # mentor może wybrać studenta
    path("mentor/", views.chat_mentor, name="chat_mentor_default"),
    path("mentor/<int:student_id>/", views.chat_mentor, name="chat_mentor"),
]