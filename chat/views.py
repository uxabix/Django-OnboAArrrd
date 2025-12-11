from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Messages
# Create your views here.
@login_required
def chat(request):
    user = request.user
    # Pobieramy wszystkie wiadomości, gdzie użytkownik jest nadawcą lub odbiorcą
    messages = Messages.objects.filter(sender=user) | Messages.objects.filter(receiver=user)
    messages = messages.order_by('sent_at')  # sortujemy po dacie wysłania

    return render(request, "chat/chat.html", {"messages": messages})