import json
import logging
from datetime import datetime
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.paginator import Paginator
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Room, Message

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatConsumer(WebsocketConsumer):
    """Базовый консьюмер для тестирования чата"""

    def connect(self):
        """Подключение к WebSocket"""
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]

        # Присоединяемся к группе комнаты
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()
        logger.info(f"User {self.user} connected to room {self.room_name}")

    def disconnect(self, close_code):
        """Отключение от WebSocket"""
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )
        logger.info(f"User {self.user} disconnected from room {self.room_name}")

    def receive(self, text_data):
        """Получение сообщения от клиента"""
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json["message"]

            # Получаем или создаем комнату
            room, created = Room.objects.get_or_create(name=self.room_name)

            # Создаем сообщение, если пользователь авторизован
            if self.user.is_authenticated:
                msg_obj = Message.objects.create(
                    room=room,
                    author=self.user,
                    content=message
                )

            # Отправляем сообщение в группу
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "chat_message",
                    "message": message,
                    "author": self.user.username if self.user.is_authenticated else "Anonymous",
                    "timestamp": timezone.now().isoformat(),
                }
            )

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def chat_message(self, event):
        """Отправка сообщения клиенту"""
        self.send(text_data=json.dumps({
            "message": event["message"],
            "author": event["author"],
            "timestamp": event["timestamp"],
        }))
