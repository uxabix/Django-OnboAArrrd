from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Messages
from .forms import MessageForm
# chat/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Messages
from .forms import MessageForm


@login_required
def chat_student(request):
    user = request.user
    
    if user.mentor is None:
        return render(request, "exceptions/no_mentor.html")  # opcjonalnie zwróć info brak mentora
    
    mentor = user.mentor

    # Obsługa formularza wysyłania wiadomości
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = user
            msg.receiver = mentor
            msg.save()
            return redirect('chat:chat_student')
    else:
        form = MessageForm()

    # Pobranie wiadomości student ↔ mentor
    messages = Messages.objects.filter(
        sender=user, receiver=mentor
    ) | Messages.objects.filter(
        sender=mentor, receiver=user
    )

    messages = messages.order_by("sent_at")

    return render(request, "chat/chat_student.html", {
        "messages": messages,
        "form": form,
        "mentor": mentor,
    })

@login_required
def chat_mentor(request, student_id=None):
    mentor = request.user

    # Pobranie wszystkich studentów, którzy mają tego mentora
    students = mentor.mentees.all()

    if not students.exists():
        return render(request, "exceptions/no_students.html")

    # Jeśli mentor nie wybrał studenta, domyślnie wybierz pierwszego
    if student_id is None:
        selected_student = students.first()
    else:
        selected_student = students.filter(id=student_id).first()

    if selected_student is None:
        return render(request, "exceptions/no_student_found.html")

    # Obsługa wysyłania wiadomości
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = mentor
            msg.receiver = selected_student
            msg.save()
            return redirect('chat:chat_mentor', student_id=selected_student.id)
    else:
        form = MessageForm()

    # Wiadomości mentor ↔ wybrany student
    messages = Messages.objects.filter(
        sender=mentor, receiver=selected_student
    ) | Messages.objects.filter(
        sender=selected_student, receiver=mentor
    )

    messages = messages.order_by("sent_at")

    return render(request, "chat/chat_mentor.html", {
        "students": students,
        "selected_student": selected_student,
        "messages": messages,
        "form": form,
    })
