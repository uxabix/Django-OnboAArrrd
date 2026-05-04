import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from .models import Messages


User = get_user_model()


def _display_name(user):
    full = f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip()
    return full or user.email


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return

        self.other_user_id = int(self.scope["url_route"]["kwargs"]["user_id"])
        if self.user.id == self.other_user_id:
            await self.close()
            return

        self.room_name = f"chat_{min(self.user.id, self.other_user_id)}_{max(self.user.id, self.other_user_id)}"
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "").strip()
        if not message:
            return

        receiver = await User.objects.aget(id=self.other_user_id)
        msg = await Messages.objects.acreate(
            sender=self.user,
            receiver=receiver,
            text=message
        )

        # wysyłka do grupy
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "id": msg.message_id,
                "message": message,
                "sender": self.user.email,
                "sender_label": _display_name(self.user),
                "sent_at": msg.sent_at.strftime("%d.%m %H:%M"),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "id": event.get("id"),
            "message": event["message"],
            "sender": event["sender"],
            "sender_label": event.get("sender_label", event["sender"]),
            "sent_at": event.get("sent_at", "teraz"),
        }))