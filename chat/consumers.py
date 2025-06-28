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
            elif message_type == 'delete_message':
                self.handle_delete_message(data)
            elif message_type == 'edit_message':
                self.handle_edit_message(data)
            elif message_type == 'forward_message':
                self.handle_forward_message(data)
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

    def handle_delete_message(self, data):
        """Обработка удаления сообщения"""
        message_id = data.get('message_id')

        if not message_id:
            logger.warning("Delete request without message_id")
            return

        try:
            # Получаем сообщение
            message = Message.objects.get(id=message_id)

            # Проверяем права: владелец может удалять любые сообщения,
            # модераторы могут удалять любые, обычные пользователи - только свои
            can_delete = (
                message.author == self.user or  # Собственное сообщение
                self.user.role == 'owner' or    # Владелец может всё
                self.user.role == 'moderator'   # Модератор может всё
            )

            if not can_delete:
                logger.warning(f"User {self.user.username} tried to delete message {message_id} without permission")
                return

            # Помечаем сообщение как удаленное (soft delete)
            message.content = "[Сообщение удалено]"
            message.is_deleted = True  # Добавим это поле позже в миграции
            message.save()

            # Уведомляем всех пользователей об удалении
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "message_deleted",
                    "message_id": str(message_id),
                    "deleted_by": self.user.username
                }
            )

            logger.info(f"Message {message_id} deleted by {self.user.username}")

        except Message.DoesNotExist:
            logger.warning(f"Attempted to delete non-existent message {message_id}")

    def handle_edit_message(self, data):
        """Обработка редактирования сообщения"""
        message_id = data.get('message_id')
        new_content = data.get('new_content', '').strip()

        if not message_id or not new_content:
            logger.warning("Edit request without message_id or new_content")
            return

        try:
            # Получаем сообщение
            message = Message.objects.get(id=message_id)

            # Проверяем права: владелец может редактировать любые сообщения,
            # модераторы могут редактировать любые, обычные пользователи - только свои
            can_edit = (
                message.author == self.user or  # Собственное сообщение
                self.user.role == 'owner' or    # Владелец может всё
                self.user.role == 'moderator'   # Модератор может всё
            )

            if not can_edit:
                logger.warning(f"User {self.user.username} tried to edit message {message_id} without permission")
                return

            # Сохраняем оригинальный контент для истории
            original_content = message.content

            # Обновляем сообщение
            message.content = new_content
            message.is_edited = True  # Добавим это поле позже в миграции
            message.edited_by = self.user
            message.edited_at = timezone.now()
            message.save()

            # Уведомляем всех пользователей об изменении
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "message_edited",
                    "message_id": str(message_id),
                    "new_content": new_content,
                    "edited_by": self.user.username,
                    "edited_by_role": self.user.role,
                    "edited_at": timezone.now().isoformat()
                }
            )

            logger.info(f"Message {message_id} edited by {self.user.username}")

        except Message.DoesNotExist:
            logger.warning(f"Attempted to edit non-existent message {message_id}")

    def handle_forward_message(self, data):
        """Обработка пересылки сообщения"""
        message_id = data.get('message_id')
        target_room_name = data.get('target_room')
        original_content = data.get('original_content', '')
        original_author = data.get('original_author', '')

        if not message_id or not target_room_name:
            logger.warning("Forward request without message_id or target_room")
            return

        try:
            # Получаем оригинальное сообщение для проверки
            original_message = Message.objects.get(id=message_id)

            # Получаем или создаем целевую комнату
            target_room, created = Room.objects.get_or_create(name=target_room_name)

            # Проверяем права доступа к целевой комнате
            can_access_target = self.check_room_access(target_room_name)
            if not can_access_target:
                logger.warning(f"User {self.user.username} tried to forward to {target_room_name} without access")
                return

            # Улучшенная логика: извлекаем чистый контент если сообщение уже пересланное
            clean_content = self.extract_clean_content(original_content)
            source_author = self.extract_original_author(original_content, original_author)

            # Определяем название источника для дисплея
            room_display_names = {
                'general': 'Беседка',
                'vip': 'Беседка - VIP',
                'moderator': 'Модераторы'
            }
            source_room_display = room_display_names.get(self.room_name, self.room_name)

            # Создаем четко структурированное пересланное сообщение
            forwarded_content = f"""📤 Переслано из «{source_room_display}»

{source_author}: {clean_content}"""

            forwarded_message = Message.objects.create(
                room=target_room,
                author=self.user,
                content=forwarded_content,
                is_forwarded=True,  # Добавим это поле позже в миграции
                original_message_id=message_id
            )

            # Отправляем сообщение в целевую группу
            target_group_name = f"chat_{target_room_name}"
            async_to_sync(self.channel_layer.group_send)(
                target_group_name, {
                    "type": "new_message",
                    "message": self.message_to_json_for_room(forwarded_message, target_room_name)
                }
            )

            logger.info(f"Message {message_id} forwarded by {self.user.username} to {target_room_name}")

        except Message.DoesNotExist:
            logger.warning(f"Attempted to forward non-existent message {message_id}")

    def extract_clean_content(self, content):
        """Извлекает чистый контент из пересланного сообщения"""
        # Если сообщение уже пересланное, извлекаем оригинальный контент
        if content.startswith('📤'):
            # Ищем последнее двоеточие после имени автора
            lines = content.split('\n')
            if len(lines) >= 3:
                # Формат: "📤 Переслано из...", "", "Автор: контент"
                author_line = lines[2]  # Третья строка с автором и контентом
                if ': ' in author_line:
                    return author_line.split(': ', 1)[1]  # Берем все после первого ": "

        return content

    def extract_original_author(self, content, fallback_author):
        """Извлекает оригинального автора из пересланного сообщения"""
        # Если сообщение уже пересланное, извлекаем оригинального автора
        if content.startswith('📤'):
            lines = content.split('\n')
            if len(lines) >= 3:
                author_line = lines[2]  # Третья строка с автором и контентом
                if ': ' in author_line:
                    return author_line.split(': ', 1)[0]  # Берем все до первого ": "

        return fallback_author

    def check_room_access(self, room_name):
        """Проверка доступа пользователя к комнате"""
        if room_name == 'general':
            return True  # Все имеют доступ к общему чату
        elif room_name == 'vip':
            return self.user.role in ['owner', 'moderator', 'vip_user']
        elif room_name == 'moderator':
            return self.user.role in ['owner', 'moderator']
        else:
            return False  # Неизвестная комната

    def message_to_json_for_room(self, message, room_name):
        """Конвертация сообщения в JSON для конкретной комнаты"""
        # Определяем является ли сообщение собственным для пользователей в целевой комнате
        reply_data = None
        if message.parent:
            reply_data = {
                'id': str(message.parent.id),
                'author_name': message.parent.author.display_name,
                'author_role_icon': message.parent.author.get_role_icon,
                'content_snippet': message.parent.content[:100] + ('...' if len(message.parent.content) > 100 else '')
            }

        return {
            'id': str(message.id),
            'content': message.content,
            'author_name': message.author.display_name,
            'author_role': message.author.role,
            'author_role_icon': message.author.get_role_icon,
            'created': message.created_at.isoformat(),
            'is_own': message.author == self.user,  # Для отправителя будет True
            'reply_to': reply_data,
            'is_reply_to_me': bool(message.parent and message.parent.author == self.user),
            'likes_count': 0,  # Заглушка для реакций
            'dislikes_count': 0,  # Заглушка для реакций
            'is_forwarded': getattr(message, 'is_forwarded', False),
            'is_edited': getattr(message, 'is_edited', False),
            'edited_by': getattr(message, 'edited_by', None).username if getattr(message, 'edited_by', None) else None,
            'edited_by_role': getattr(message, 'edited_by', None).role if getattr(message, 'edited_by', None) else None,
        }

    def message_to_json(self, message, is_history=False):
        """Конвертация сообщения в JSON с поддержкой ответов и редактирования"""
        reply_data = None
        if message.parent:
            reply_data = {
                'id': str(message.parent.id),
                'author_name': message.parent.author.display_name,
                'author_role_icon': message.parent.author.get_role_icon,
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
            'is_edited': getattr(message, 'is_edited', False),
            'edited_by': getattr(message, 'edited_by', None).username if getattr(message, 'edited_by', None) else None,
            'edited_by_role': getattr(message, 'edited_by', None).role if getattr(message, 'edited_by', None) else None,
            'edited_at': getattr(message, 'edited_at', None).isoformat() if getattr(message, 'edited_at', None) else None,
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

    # Обработчики событий группы для новых типов сообщений
    def message_deleted(self, event):
        """Уведомление об удалении сообщения"""
        self.send(text_data=json.dumps({
            "type": "message_deleted",
            "message_id": event["message_id"],
            "deleted_by": event["deleted_by"]
        }))

    def message_edited(self, event):
        """Уведомление об изменении сообщения"""
        self.send(text_data=json.dumps({
            "type": "message_edited",
            "message_id": event["message_id"],
            "new_content": event["new_content"],
            "edited_by": event["edited_by"],
            "edited_by_role": event["edited_by_role"],
            "edited_at": event["edited_at"]
        }))


# Алиас для обратной совместимости
class ChatConsumer(BaseChatConsumer):
    """Алиас для обратной совместимости"""
    pass
