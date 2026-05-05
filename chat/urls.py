from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    # New universal chat (any user <-> any user)
    path("", views.chat_inbox, name="chat_inbox"),
    path("updates/<int:user_id>/", views.chat_updates, name="chat_updates"),
    path("<int:user_id>/", views.chat_inbox, name="chat_inbox_user"),

    # Backward-compatible routes
    path("student/", views.chat_student, name="chat_student"),
    path("mentor/", views.chat_mentor, name="chat_mentor_default"),
    path("mentor/<int:student_id>/", views.chat_mentor, name="chat_mentor"),
]