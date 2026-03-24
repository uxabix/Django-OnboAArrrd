from django.db import models
from django.utils import timezone

from OnboAArrrd import settings

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

    text = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['sent_at']
