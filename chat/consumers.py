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


class BaseChatConsumer(WebsocketConsumer):
    """Базовый консьюмер для кастомного чата "Беседка" с поддержкой системы ответов"""

    def connect(self):
        """Подключение к WebSocket"""
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            self.close()
            return

        # Присоединяемся к группе комнаты
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()
        logger.info(f"User {self.user.username} connected to room {self.room_name}")

        # Уведомляем группу о присоединении пользователя
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {
                "type": "user_joined",
                "user": self.user_to_json(self.user)
            }
        )

    def disconnect(self, close_code):
        """Отключение от WebSocket"""
        if hasattr(self, 'room_group_name'):
            # Уведомляем группу об отключении пользователя
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "user_left",
                    "user": self.user_to_json(self.user)
                }
            )

            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name, self.channel_name
            )
        logger.info(f"User {self.user.username} disconnected from room {self.room_name}")

    def receive(self, text_data):
        """Получение сообщений от клиента с поддержкой различных типов"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')

            if message_type == 'message':
                self.handle_chat_message(data)
            elif message_type == 'fetch_messages':
                self.send_message_history(data.get('page', 1))
            elif message_type == 'fetch_online_users':
                self.send_online_users()
            elif message_type == 'typing':
                self.handle_typing(data)
            elif message_type == 'reaction':
                self.handle_reaction(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def handle_chat_message(self, data):
        """Обработка текстового сообщения с поддержкой ответов"""
        content = data.get('message', '').strip()
        reply_to_id = data.get('reply_to_id')

        if not content:
            return

        # Получаем или создаем комнату
        room, created = Room.objects.get_or_create(name=self.room_name)

        # Обрабатываем ответ на сообщение
        parent_message = None
        if reply_to_id:
            try:
                parent_message = Message.objects.get(id=reply_to_id, room=room)
            except Message.DoesNotExist:
                logger.warning(f"Reply target message {reply_to_id} not found")

        # Создаем сообщение
        message = Message.objects.create(
            room=room,
            author=self.user,
            content=content,
            parent=parent_message
        )

        # Отправляем сообщение в группу
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {
                "type": "new_message",
                "message": self.message_to_json(message)
            }
        )

    def send_message_history(self, page=1):
        """Отправка истории сообщений с поддержкой ответов"""
        try:
            room, created = Room.objects.get_or_create(name=self.room_name)

            # Получаем последние 50 сообщений с related данными
            messages = Message.objects.filter(room=room).select_related(
                'author', 'parent', 'parent__author'
            ).order_by('-created_at')[:50]

            # Обращаем порядок и конвертируем в JSON
            messages_data = [
                self.message_to_json(msg, is_history=True)
                for msg in reversed(messages)
            ]

            self.send(text_data=json.dumps({
                "type": "messages_history",
                "messages": messages_data
            }))

        except Exception as e:
            logger.error(f"Error sending message history: {e}")

    def send_online_users(self):
        """Отправка списка онлайн пользователей"""
        # Примитивная реализация - можно улучшить с Redis
        online_users = [
            self.user_to_json(self.user)
        ]

        self.send(text_data=json.dumps({
            "type": "online_users",
            "users": online_users,
            "count": len(online_users)
        }))

    def handle_typing(self, data):
        """Обработка индикатора печати"""
        is_typing = data.get('is_typing', False)

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {
                "type": "typing_indicator",
                "user": self.user.username,
                "is_typing": is_typing
            }
        )

    def handle_reaction(self, data):
        """Обработка реакций на сообщения (заглушка)"""
        # Реализация реакций будет в следующих этапах
        message_id = data.get('message_id')
        reaction = data.get('reaction')
        logger.info(f"Reaction {reaction} on message {message_id} by {self.user.username}")

    def message_to_json(self, message, is_history=False):
        """Конвертация сообщения в JSON с поддержкой ответов"""
        reply_data = None
        if message.parent:
            reply_data = {
                'id': str(message.parent.id),
                'author_name': message.parent.author.display_name,
                'content_snippet': message.parent.content[:100] + ('...' if len(message.parent.content) > 100 else '')
            }

        return {
            'id': str(message.id),
            'content': message.content,
            'author_name': message.author.display_name,
            'author_role': message.author.role,
            'author_role_icon': message.author.get_role_icon,
            'created': message.created_at.isoformat(),
            'is_own': message.author == self.user,
            'reply_to': reply_data,
            'is_reply_to_me': bool(message.parent and message.parent.author == self.user),
            'likes_count': 0,  # Заглушка для реакций
            'dislikes_count': 0,  # Заглушка для реакций
        }

    def user_to_json(self, user):
        """Конвертация пользователя в JSON"""
        return {
            'username': user.username,
            'display_name': user.display_name,
            'role': user.role,
            'role_icon': user.get_role_icon,
        }

    # Обработчики событий группы
    def new_message(self, event):
        """Отправка нового сообщения клиенту"""
        self.send(text_data=json.dumps({
            "type": "new_message",
            "message": event["message"]
        }))

    def user_joined(self, event):
        """Уведомление о присоединении пользователя"""
        self.send(text_data=json.dumps({
            "type": "user_joined",
            "user": event["user"]
        }))

    def user_left(self, event):
        """Уведомление об отключении пользователя"""
        self.send(text_data=json.dumps({
            "type": "user_left",
            "user": event["user"]
        }))

    def typing_indicator(self, event):
        """Отправка индикатора печати"""
        # Не отправляем самому себе
        if event["user"] != self.user.username:
            self.send(text_data=json.dumps({
                "type": "typing",
                "user": event["user"],
                "is_typing": event["is_typing"]
            }))


# Алиас для обратной совместимости
class ChatConsumer(BaseChatConsumer):
    """Алиас для обратной совместимости"""
    pass
