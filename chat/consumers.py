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
            elif message_type == 'edit_message':
                self.handle_edit_message(data)
            elif message_type == 'delete_message':
                self.handle_delete_message(data)
            elif message_type == 'forward_message':
                self.handle_forward_message(data)
            elif message_type == 'pin_message':
                self.handle_pin_message(data)
            elif message_type == 'unpin_message':
                self.handle_unpin_message(data)
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

            # Получаем последние 50 сообщений с related данными (ИСКЛЮЧАЕМ УДАЛЕННЫЕ!)
            messages = Message.objects.filter(room=room, is_deleted=False).select_related(
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

    def handle_edit_message(self, data):
        """Обработка редактирования сообщения с проверкой прав доступа"""
        message_id = data.get('message_id')
        new_content = data.get('new_content', '').strip()

        if not message_id or not new_content:
            self.send_error("Недостаточно данных для редактирования")
            return

        try:
            # Получаем сообщение
            room, _ = Room.objects.get_or_create(name=self.room_name)
            message = Message.objects.get(id=message_id, room=room, is_deleted=False)

            # 🎯 ПРОВЕРКА ПРАВ ДОСТУПА (согласно требованиям)
            can_edit = self.can_edit_message(message)
            if not can_edit:
                self.send_error("У вас нет прав на редактирование этого сообщения")
                return

            # Сохраняем оригинальный контент для логирования
            original_content = message.content

            # Обновляем сообщение
            message.content = new_content
            message.is_edited = True
            message.edited_by = self.user
            message.edited_at = timezone.now()
            message.save()

            # Отправляем обновленное сообщение всем в группе
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "message_edited",
                    "message": self.message_to_json(message),
                    "editor": self.user_to_json(self.user)
                }
            )

            logger.info(f"Message {message_id} edited by {self.user.username}. " +
                       f"Original: '{original_content[:50]}...' -> New: '{new_content[:50]}...'")

        except Message.DoesNotExist:
            self.send_error("Сообщение не найдено или уже удалено")
        except Exception as e:
            logger.error(f"Error editing message {message_id}: {e}")
            self.send_error("Ошибка при редактировании сообщения")

    def handle_delete_message(self, data):
        """Обработка удаления сообщения с проверкой прав доступа"""
        message_id = data.get('message_id')

        if not message_id:
            self.send_error("ID сообщения не указан")
            return

        try:
            # Получаем сообщение
            room, _ = Room.objects.get_or_create(name=self.room_name)
            message = Message.objects.get(id=message_id, room=room, is_deleted=False)

            # 🎯 ПРОВЕРКА ПРАВ ДОСТУПА (согласно требованиям)
            can_delete = self.can_delete_message(message)
            if not can_delete:
                self.send_error("У вас нет прав на удаление этого сообщения")
                return

            # Мягкое удаление сообщения
            message.is_deleted = True
            message.content = "[Сообщение удалено]"
            message.edited_by = self.user
            message.edited_at = timezone.now()
            message.save()

            # Отправляем уведомление об удалении всем в группе
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "message_deleted",
                    "message_id": str(message_id),
                    "deleted_by": self.user_to_json(self.user)
                }
            )

            logger.info(f"Message {message_id} deleted by {self.user.username}")

        except Message.DoesNotExist:
            self.send_error("Сообщение не найдено или уже удалено")
        except Exception as e:
            logger.error(f"Error deleting message {message_id}: {e}")
            self.send_error("Ошибка при удалении сообщения")

    def handle_forward_message(self, data):
        """Обработка пересылки сообщения с поддержкой пользовательского текста"""
        message_id = data.get('message_id')
        target_room = data.get('target_room', self.room_name)
        custom_message = data.get('custom_message', '').strip()

        if not message_id:
            self.send_error("ID сообщения не указан")
            return

        try:
            # Получаем оригинальное сообщение
            source_room, _ = Room.objects.get_or_create(name=self.room_name)
            original_message = Message.objects.get(id=message_id, room=source_room, is_deleted=False)

            # Получаем комнату назначения
            target_room_obj, _ = Room.objects.get_or_create(name=target_room)

            # Извлекаем чистый контент и автора
            clean_content = self.extract_clean_content(original_message.content)
            original_author = self.extract_original_author(original_message.content, original_message.author.display_name)

            # Определяем отображаемое название источника
            if self.room_name == "general":
                source_room_display = "Беседка"
            elif self.room_name == "vip":
                source_room_display = "Беседка - VIP"
            elif self.room_name == "moderators":
                source_room_display = "Модераторы"
            else:
                # Для любых других комнат используем более читаемое название
                source_room_display = f"Чат «{self.room_name.title()}»"

            # 💬 СОЗДАЕМ ФИНАЛЬНЫЙ КОНТЕНТ БЕЗ ДУБЛИРОВАНИЯ ИНФОРМАЦИИ О ПЕРЕСЫЛКЕ
            # Формируем правильную информацию об авторе оригинального сообщения
            original_author_with_icon = f"{original_message.author.get_role_icon} {original_message.author.display_name}"

            if custom_message:
                # Если есть пользовательское сообщение, пересланный контент становится цитатой
                forwarded_content = f"""{custom_message}

📤 Переслано из «{source_room_display}» • {self.user.get_role_icon} {self.user.display_name}
{original_author_with_icon}
{clean_content}"""
            else:
                # Если нет пользовательского сообщения, используем стандартный формат
                forwarded_content = f"""📤 Переслано из «{source_room_display}» • {self.user.get_role_icon} {self.user.display_name}
{original_author_with_icon}
{clean_content}"""

            # Создаем новое сообщение
            forwarded_message = Message.objects.create(
                room=target_room_obj,
                author=self.user,
                content=forwarded_content,
                is_forwarded=True,
                original_message_id=str(message_id)
            )

            # Отправляем пересланное сообщение в группу ЦЕЛЕВОГО ЧАТА
            target_group_name = f"chat_{target_room}"
            async_to_sync(self.channel_layer.group_send)(
                target_group_name, {
                    "type": "message_forwarded",
                    "message": self.message_to_json(forwarded_message),
                    "forwarder": self.user_to_json(self.user)
                }
            )

            if custom_message:
                logger.info(f"Message {message_id} forwarded by {self.user.username} to {target_room} with custom message")
            else:
                logger.info(f"Message {message_id} forwarded by {self.user.username} to {target_room}")

        except Message.DoesNotExist:
            self.send_error("Сообщение не найдено или уже удалено")
        except Exception as e:
            logger.error(f"Error forwarding message {message_id}: {e}")
            self.send_error("Ошибка при пересылке сообщения")

    def handle_pin_message(self, data):
        """Обработка закрепления сообщения с проверкой прав доступа"""
        message_id = data.get('message_id')

        if not message_id:
            self.send_error("ID сообщения не указан")
            return

        try:
            # Получаем сообщение
            room, _ = Room.objects.get_or_create(name=self.room_name)
            message = Message.objects.get(id=message_id, room=room, is_deleted=False)

            # 🎯 ПРОВЕРКА ПРАВ ДОСТУПА НА ЗАКРЕПЛЕНИЕ
            can_pin = self.can_pin_message(message)
            if not can_pin:
                self.send_error("У вас нет прав на закрепление сообщений")
                return

            # Закрепляем сообщение
            message.is_pinned = True
            message.pinned_by = self.user
            message.pinned_at = timezone.now()
            message.save()

            # Отправляем уведомление о закреплении всем в группе
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "message_pinned",
                    "message_id": str(message_id),
                    "pinner": self.user_to_json(self.user)
                }
            )

            logger.info(f"Message {message_id} pinned by {self.user.username}")

        except Message.DoesNotExist:
            self.send_error("Сообщение не найдено или уже удалено")
        except Exception as e:
            logger.error(f"Error pinning message {message_id}: {e}")
            self.send_error("Ошибка при закреплении сообщения")

    def handle_unpin_message(self, data):
        """Обработка открепления сообщения с проверкой прав доступа"""
        message_id = data.get('message_id')

        if not message_id:
            self.send_error("ID сообщения не указан")
            return

        try:
            # Получаем сообщение
            room, _ = Room.objects.get_or_create(name=self.room_name)
            message = Message.objects.get(id=message_id, room=room, is_deleted=False)

            # 🎯 ПРОВЕРКА ПРАВ ДОСТУПА НА ОТКРЕПЛЕНИЕ
            can_pin = self.can_pin_message(message)
            if not can_pin:
                self.send_error("У вас нет прав на открепление сообщений")
                return

            # Открепляем сообщение
            message.is_pinned = False
            message.pinned_by = None
            message.pinned_at = None
            message.save()

            # Отправляем уведомление об откреплении всем в группе
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "message_unpinned",
                    "message_id": str(message_id),
                    "unpinner": self.user_to_json(self.user)
                }
            )

            logger.info(f"Message {message_id} unpinned by {self.user.username}")

        except Message.DoesNotExist:
            self.send_error("Сообщение не найдено или уже удалено")
        except Exception as e:
            logger.error(f"Error unpinning message {message_id}: {e}")
            self.send_error("Ошибка при откреплении сообщения")

    def can_edit_message(self, message):
        """Проверка прав на редактирование сообщения"""
        user_role = self.user.role
        message_author_role = message.author.role

        # 👑 Owner может редактировать ВСЕ сообщения
        if user_role == 'owner':
            return True
        # 🎭 Moderator/Admin может редактировать любые КРОМЕ owner
        elif user_role in ['moderator', 'admin']:
            return message_author_role != 'owner'
        # 👤 Остальные только свои сообщения
        else:
            return message.author == self.user

    def can_delete_message(self, message):
        """Проверка прав на удаление сообщения"""
        user_role = self.user.role
        message_author_role = message.author.role

        # 👑 Owner может удалять ВСЕ сообщения
        if user_role == 'owner':
            return True
        # 🎭 Moderator/Admin может удалять любые КРОМЕ owner
        elif user_role in ['moderator', 'admin']:
            return message_author_role != 'owner'
        # 👤 Остальные только свои сообщения
        else:
            return message.author == self.user

    def can_pin_message(self, message):
        """Проверка прав на закрепление сообщения"""
        user_role = self.user.role

        # 👑 Owner и 🎭 Moderator/Admin могут закреплять сообщения
        if user_role in ['owner', 'moderator', 'admin']:
            return True
        # 👤 Остальные не могут закреплять
        else:
            return False

    def extract_clean_content(self, content):
        """Извлекает чистый контент из пересланного сообщения"""
        lines = content.strip().split('\n')

        if len(lines) < 3:
            return content

        # Ищем строку с автором (начинается с emoji или содержит имя)
        for i, line in enumerate(lines):
            if i > 0 and line.strip() and not line.startswith('Переслано') and not line.startswith('📤'):
                # Возвращаем все что после автора
                return '\n'.join(lines[i+1:]).strip()

        return content

    def extract_original_author(self, content, fallback_author):
        """Извлекает оригинального автора из пересланного сообщения"""
        lines = content.strip().split('\n')

        if len(lines) < 2:
            return fallback_author

        # Ищем строку с автором (вторая строка в нашем формате)
        for i, line in enumerate(lines):
            if i > 0 and line.strip() and not line.startswith('Переслано') and not line.startswith('📤'):
                return line.strip()

        return fallback_author

    def send_error(self, error_message):
        """Отправка сообщения об ошибке клиенту"""
        self.send(text_data=json.dumps({
            "type": "error",
            "message": error_message
        }))

    def message_to_json(self, message, is_history=False):
        """Конвертация сообщения в JSON с поддержкой ответов"""
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
            'is_edited': message.is_edited,
            'edited_by': message.edited_by.display_name if message.edited_by else None,
            'edited_by_role': message.edited_by.role if message.edited_by else None,
            'edited_at': message.edited_at.isoformat() if message.edited_at else None,
            'is_pinned': message.is_pinned,
            'pinned_by': message.pinned_by.display_name if message.pinned_by else None,
            'pinned_at': message.pinned_at.isoformat() if message.pinned_at else None,
            'is_forwarded': getattr(message, 'is_forwarded', False),
            'original_message_id': getattr(message, 'original_message_id', None),
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

    def message_edited(self, event):
        """Уведомление о редактировании сообщения"""
        self.send(text_data=json.dumps({
            "type": "message_edited",
            "message": event["message"],
            "editor": event["editor"]
        }))

    def message_deleted(self, event):
        """Уведомление об удалении сообщения"""
        self.send(text_data=json.dumps({
            "type": "message_deleted",
            "message_id": event["message_id"],
            "deleted_by": event["deleted_by"]
        }))

    def message_forwarded(self, event):
        """Уведомление о пересылке сообщения"""
        self.send(text_data=json.dumps({
            "type": "message_forwarded",
            "message": event["message"],
            "forwarder": event["forwarder"]
        }))

    def message_pinned(self, event):
        """Уведомление о закреплении сообщения"""
        self.send(text_data=json.dumps({
            "type": "message_pinned",
            "message_id": event["message_id"],
            "pinner": event["pinner"]
        }))

    def message_unpinned(self, event):
        """Уведомление об откреплении сообщения"""
        self.send(text_data=json.dumps({
            "type": "message_unpinned",
            "message_id": event["message_id"],
            "unpinner": event["unpinner"]
        }))


# Алиас для обратной совместимости
class ChatConsumer(BaseChatConsumer):
    """Алиас для обратной совместимости"""
    pass
