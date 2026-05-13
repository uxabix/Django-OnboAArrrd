"""Django Channels consumer bridging websocket chat to persistent messages."""

import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from onboarding.models import User_paths, User_tasks
from .models import Messages


User = get_user_model()


def _display_name(user):
    """Format ``user`` similar to :func:`chat.views._display_name`."""

    full = f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip()
    return full or user.email


class ChatConsumer(AsyncWebsocketConsumer):
    """Websocket endpoint mirroring HTTP chat scopes for live updates."""

    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return

        self.other_user_id = int(self.scope["url_route"]["kwargs"]["user_id"])
        if self.user.id == self.other_user_id:
            await self.close()
            return

        query_data = parse_qs(self.scope.get("query_string", b"").decode())
        self.ctx_type = (query_data.get("ctx_type", [""])[0] or "").strip().lower()
        self.ctx_id = (query_data.get("ctx_id", [""])[0] or "").strip()
        self.user_task = None
        self.user_path = None

        try:
            if self.ctx_type and self.ctx_id.isdigit():
                if self.ctx_type == "task":
                    self.user_task = await User_tasks.objects.select_related("user_id", "assigned_by").aget(pk=int(self.ctx_id))
                    participants = {self.user_task.user_id_id, self.user_task.assigned_by_id}
                    if self.user.id not in participants or self.other_user_id not in participants:
                        await self.close()
                        return
                elif self.ctx_type == "path":
                    self.user_path = await User_paths.objects.select_related("user", "assigned_by").aget(pk=int(self.ctx_id))
                    participants = {self.user_path.user_id, self.user_path.assigned_by_id}
                    if self.user.id not in participants or self.other_user_id not in participants:
                        await self.close()
                        return
                else:
                    self.ctx_type = ""
                    self.ctx_id = ""
        except (User_tasks.DoesNotExist, User_paths.DoesNotExist):
            await self.close()
            return

        context_room = "general"
        if self.ctx_type and self.ctx_id:
            context_room = f"{self.ctx_type}_{self.ctx_id}"
        self.room_name = f"chat_{min(self.user.id, self.other_user_id)}_{max(self.user.id, self.other_user_id)}_{context_room}"
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        """Leave the channel layer group when the socket closes."""

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Persist inbound JSON messages and broadcast them to the room group.

        Args:
            text_data: JSON string containing a ``message`` field.
        """
        data = json.loads(text_data)
        message = data.get("message", "").strip()
        if not message:
            return

        receiver = await User.objects.aget(id=self.other_user_id)
        msg = await Messages.objects.acreate(
            sender=self.user,
            receiver=receiver,
            text=message,
            user_task=self.user_task,
            user_path=self.user_path,
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
        """Fan-out handler invoked by ``channel_layer.group_send``."""

        await self.send(text_data=json.dumps({
            "id": event.get("id"),
            "message": event["message"],
            "sender": event["sender"],
            "sender_label": event.get("sender_label", event["sender"]),
            "sent_at": event.get("sent_at", "teraz"),
        }))