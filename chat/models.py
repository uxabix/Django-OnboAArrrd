from django.db import models
from django.contrib.auth import get_user_model

CustomUser = get_user_model()
# Create your models here.
class Message(models.Model):
    message_id = models.BigAutoField(primary_key=True)
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="received_messages"
    )

    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']
