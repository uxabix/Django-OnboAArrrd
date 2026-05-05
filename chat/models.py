from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from OnboAArrrd import settings
from onboarding.models import User_paths, User_tasks

CustomUser = get_user_model()
# Create your models here.
class Messages(models.Model):
    message_id = models.BigAutoField(primary_key=True)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_messages"
    )
    user_task = models.ForeignKey(
        User_tasks,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        blank=True,
        null=True,
    )
    user_path = models.ForeignKey(
        User_paths,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        blank=True,
        null=True,
    )

    text = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['sent_at']
