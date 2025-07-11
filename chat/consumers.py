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

from .models import Room, Message, UserChatPosition

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseChatConsumer(WebsocketConsumer):
    """Базовый консьюмер для кастомного чата "Беседка" с поддержкой системы ответов"""

    def connect(self):
        """Подключение к WebSocket"""
        # room_name должен быть установлен дочерним классом перед вызовом super().connect()
        if not hasattr(self, 'room_name'):
            self.close()
            return

        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            self.close()
            return

        # Добавляем пользователя в группу чата
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

        # 🔧 ИСПРАВЛЕНО: Правильная последовательность инициализации позиции
        room, _ = Room.objects.get_or_create(name=self.room_name)
        position = UserChatPosition.get_or_create_for_user(self.user, room)

        # 🎯 НОВАЯ ЛОГИКА: Определяем, является ли это первым визитом
        is_first_visit = position.last_visit_at is None

        # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: При первом посещении НЕ устанавливаем last_read_at
        if is_first_visit:
            # Первый визит - устанавливаем только время визита, НЕ время прочтения
            position.last_visit_at = timezone.now()
            # НЕ устанавливаем last_read_at - пусть остается None
            # Это означает, что нет "непрочитанных" сообщений для нового пользователя
            position.save()
            logger.info(f"First visit: initialized position for {self.user.username} in {self.room_name}")
        else:
            # Обновляем время визита для следующих посещений
            position.mark_visit()
            logger.info(f"Return visit: updated visit time for {self.user.username} in {self.room_name}")

        # Обновляем position после изменений
        position.refresh_from_db()

        # 📬 ИСПРАВЛЕНО: НЕ ОТПРАВЛЯЕМ unread_info здесь - отправим ПОСЛЕ истории сообщений
        # Сохраняем позицию для позднейшего использования
        self.user_position = position

        # Уведомляем других о подключении
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {
                "type": "user_joined",
                "user": self.user_to_json(self.user)
            }
        )

        logger.info(f"User {self.user.username} connected to chat {self.room_name}")

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
            elif message_type == 'mark_as_read':
                self.handle_mark_as_read(data)
            elif message_type == 'load_more_messages':
                self.handle_load_more_messages(data)
            elif message_type == 'save_position':
                self.handle_save_position(data)
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

        # 🎯 НОВАЯ ЛОГИКА: При первом сообщении устанавливаем last_read_at
        position = UserChatPosition.get_or_create_for_user(self.user, room)
        if position.last_read_at is None:
            # Первое сообщение пользователя - теперь он "читает" чат
            position.last_read_at = timezone.now()
            position.save()
            logger.info(f"First message sent: set last_read_at for {self.user.username} in {self.room_name}")

        # 🚫 УДАЛЕНА НЕПРАВИЛЬНАЯ АВТООТМЕТКА ПРИ ОТПРАВКЕ СООБЩЕНИЯ
        # Отправка сообщения НЕ означает прочтение всей истории чата!

        # Отправляем сообщение в группу
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {
                "type": "new_message",
                "message": self.message_to_json(message)
            }
        )

    def send_message_history(self, page=1):
        """Отправка истории сообщений с поддержкой непрочитанных сообщений"""
        try:
            room, created = Room.objects.get_or_create(name=self.room_name)

            # Получаем позицию пользователя для определения непрочитанных
            user_position = UserChatPosition.get_or_create_for_user(self.user, room)

            # Получаем последние 100 сообщений с related данными (ИСКЛЮЧАЕМ УДАЛЕННЫЕ!)
            messages = Message.objects.filter(room=room, is_deleted=False).select_related(
                'author', 'parent', 'parent__author'
            ).order_by('-created_at')[:100]

            # Обращаем порядок и конвертируем в JSON
            messages_data = []
            for msg in reversed(messages):
                message_json = self.message_to_json(msg, is_history=True)

                # 🔧 ИСПРАВЛЕНО: Правильная логика определения прочитанности
                if user_position.last_read_at:
                    # Пользователь уже посещал чат - сравниваем с last_read_at
                    message_json['is_read'] = msg.created_at <= user_position.last_read_at
                else:
                    # Новый пользователь - все исторические сообщения считаются прочитанными
                    # (это исправляется в connect(), но на всякий случай)
                    message_json['is_read'] = True

                # 🎯 НОВОЕ: Отмечаем персональные уведомления
                message_json['is_personal_notification'] = msg.is_personal_notification_for(self.user)

                messages_data.append(message_json)

            # Отправляем историю сообщений
            self.send(text_data=json.dumps({
                "type": "messages_history",
                "messages": messages_data
            }))

            # 📬 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Отправляем unread_info ПОСЛЕ истории сообщений
            # Используем позицию из connect() если она есть, иначе текущую
            position_to_use = getattr(self, 'user_position', user_position)
            self.send_unread_info(position_to_use)

        except Exception as e:
            logger.error(f"Error sending message history: {e}")

    def send_online_users(self):
        """Отправка списка онлайн пользователей и общего количества пользователей с доступом"""
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # 👥 ПОДСЧЕТ ОБЩЕГО КОЛИЧЕСТВА ПОЛЬЗОВАТЕЛЕЙ С ДОСТУПОМ К ЧАТУ
        if self.room_name == 'vip':
            # VIP чат - только владельцы и администрация магазина
            total_users_count = User.objects.filter(
                role__in=['owner', 'store_owner', 'store_admin']
            ).count()
        elif self.room_name == 'moderators':
            # Чат модераторов - только модераторы и владельцы
            total_users_count = User.objects.filter(
                role__in=['owner', 'moderator']
            ).count()
        else:
            # Общий чат - все зарегистрированные пользователи
            total_users_count = User.objects.filter(is_active=True).count()

        # 🔍 ВРЕМЕННАЯ РЕАЛИЗАЦИЯ ОНЛАЙН ПОЛЬЗОВАТЕЛЕЙ
        # TODO: В будущем можно заменить на Redis или более продвинутую систему
        online_users = [
            self.user_to_json(self.user)
        ]

        self.send(text_data=json.dumps({
            "type": "online_users",
            "users": online_users,
            "count": len(online_users),
            "total_count": total_users_count  # 📊 НОВОЕ ПОЛЕ - общее количество с доступом
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
        """Обработка реакций на сообщения с сохранением в БД"""
        message_id = data.get('message_id')
        reaction_type = data.get('reaction')  # 'like' или 'dislike'

        if not message_id or not reaction_type:
            self.send_error("Недостаточно данных для реакции")
            return

        if reaction_type not in ['like', 'dislike']:
            self.send_error("Неверный тип реакции")
            return

        try:
            # Получаем сообщение
            room, _ = Room.objects.get_or_create(name=self.room_name)
            message = Message.objects.get(id=message_id, room=room, is_deleted=False)

            # Проверяем, не реагирует ли пользователь на собственное сообщение
            if message.author == self.user:
                self.send_error("Нельзя ставить реакцию на собственное сообщение")
                return

            # Импортируем модель реакций
            from .models import MessageReaction

            # Проверяем, есть ли уже реакция от этого пользователя
            existing_reaction = MessageReaction.objects.filter(
                message=message,
                user=self.user
            ).first()

            if existing_reaction:
                # Пользователь уже реагировал - отправляем ошибку
                self.send_error("Вы уже реагировали на это сообщение")
                return

            # Создаем новую реакцию
            new_reaction = MessageReaction.objects.create(
                message=message,
                user=self.user,
                reaction_type=reaction_type
            )

            # Получаем обновленные счетчики
            likes_count = message.likes_count
            dislikes_count = message.dislikes_count

            # Отправляем обновленную реакцию всем в группе
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "reaction_updated",
                    "message_id": str(message_id),
                    "reaction_type": reaction_type,
                    "user": self.user_to_json(self.user),
                    "likes_count": likes_count,
                    "dislikes_count": dislikes_count
                }
            )

        except Exception as e:
            logger.error(f"Error handling reaction: {e}")
            self.send_error("Ошибка при обработке реакции")

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
            self.send_error("Сообщение не найдено")
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            self.send_error("Ошибка при редактировании сообщения")

    def handle_delete_message(self, data):
        """Обработка удаления сообщения с проверкой прав доступа"""
        message_id = data.get('message_id')

        if not message_id:
            self.send_error("Недостаточно данных для удаления")
            return

        try:
            # Получаем сообщение
            room, _ = Room.objects.get_or_create(name=self.room_name)
            message = Message.objects.get(id=message_id, room=room, is_deleted=False)

            # 🎯 ПРОВЕРКА ПРАВ ДОСТУПА (аналогично редактированию)
            can_delete = self.can_edit_message(message)
            if not can_delete:
                self.send_error("У вас нет прав на удаление этого сообщения")
                return

            # Помечаем сообщение как удаленное (мягкое удаление)
            message.is_deleted = True
            message.save()

            # Отправляем уведомление об удалении всем в группе
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "message_deleted",
                    "message_id": str(message_id),
                    "deleter": self.user_to_json(self.user)
                }
            )

            logger.info(f"Message {message_id} deleted by {self.user.username}")

        except Message.DoesNotExist:
            self.send_error("Сообщение не найдено")
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            self.send_error("Ошибка при удалении сообщения")

    def handle_forward_message(self, data):
        """Обработка пересылки сообщения в другой чат"""
        message_id = data.get('message_id')
        target_room = data.get('target_room')
        custom_message = data.get('custom_message', '').strip()

        if not message_id or not target_room:
            self.send_error("Недостаточно данных для пересылки")
            return

        try:
            # Получаем оригинальное сообщение
            source_room, _ = Room.objects.get_or_create(name=self.room_name)
            original_message = Message.objects.get(id=message_id, room=source_room, is_deleted=False)

            # Получаем комнату назначения
            target_room_obj, _ = Room.objects.get_or_create(name=target_room)

            # 🎯 КАСКАДНАЯ ЛОГИКА ПЕРЕСЫЛКИ: Каждый уровень ссылается на предыдущий
            if original_message.is_forwarded:
                # Пересылаем уже пересланное сообщение - берем основной контент (комментарий пользователя)
                clean_content = self.extract_clean_content(original_message.content)
                # Автор ЭТОГО пересланного сообщения (кто переслал), а не оригинального
                original_author_with_icon = f"{original_message.author.get_role_icon} {original_message.author.display_name}"
            else:
                # Пересылаем обычное сообщение - берем его содержимое как есть
                clean_content = original_message.content
                original_author_with_icon = f"{original_message.author.get_role_icon} {original_message.author.display_name}"

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

            # 💬 СОЗДАЕМ ФИНАЛЬНЫЙ КОНТЕНТ В ЗАВИСИМОСТИ ОТ НАЛИЧИЯ ПОЛЬЗОВАТЕЛЬСКОГО СООБЩЕНИЯ
            if custom_message:
                # 🎯 НОВАЯ ЛОГИКА: Пользовательское сообщение + структурированная цитата пересланного
                forwarded_content = f"""{custom_message}

📤 Переслано из «{source_room_display}» • {original_author_with_icon}
{original_author_with_icon}
{clean_content}"""
            else:
                # Если нет пользовательского сообщения, используем стандартный формат
                forwarded_content = f"""📤 Переслано из «{source_room_display}» • {original_author_with_icon}
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
            self.send_error("Сообщение не найдено")
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            self.send_error("Ошибка при пересылке сообщения")

    def handle_pin_message(self, data):
        """Обработка закрепления сообщения"""
        message_id = data.get('message_id')

        if not message_id:
            self.send_error("Недостаточно данных для закрепления")
            return

        try:
            # Получаем сообщение
            room, _ = Room.objects.get_or_create(name=self.room_name)
            message = Message.objects.get(id=message_id, room=room, is_deleted=False)

            # 🎯 ПРОВЕРКА ПРАВ ДОСТУПА (только модераторы и владельцы могут закреплять)
            if self.user.role not in ['owner', 'moderator', 'admin']:
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
                    "message": self.message_to_json(message),
                    "pinner": self.user_to_json(self.user)
                }
            )

            logger.info(f"Message {message_id} pinned by {self.user.username}")

        except Message.DoesNotExist:
            self.send_error("Сообщение не найдено")
        except Exception as e:
            logger.error(f"Error pinning message: {e}")
            self.send_error("Ошибка при закреплении сообщения")

    def handle_unpin_message(self, data):
        """Обработка открепления сообщения"""
        message_id = data.get('message_id')

        if not message_id:
            self.send_error("Недостаточно данных для открепления")
            return

        try:
            # Получаем сообщение
            room, _ = Room.objects.get_or_create(name=self.room_name)
            message = Message.objects.get(id=message_id, room=room, is_deleted=False)

            # 🎯 ПРОВЕРКА ПРАВ ДОСТУПА (только модераторы и владельцы могут откреплять)
            if self.user.role not in ['owner', 'moderator', 'admin']:
                self.send_error("У вас нет прав на открепление сообщений")
                return

            # Открепляем сообщение
            message.is_pinned = False
            message.pinned_by = None
            message.pinned_at = None
            message.save()

            # Отправляем уведомление об открепленшании всем в группе
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, {
                    "type": "message_unpinned",
                    "message": self.message_to_json(message),
                    "unpinner": self.user_to_json(self.user)
                }
            )

            logger.info(f"Message {message_id} unpinned by {self.user.username}")

        except Message.DoesNotExist:
            self.send_error("Сообщение не найдено")
        except Exception as e:
            logger.error(f"Error unpinning message: {e}")
            self.send_error("Ошибка при открепленшании сообщения")

    def handle_save_position(self, data):
        """Сохранение позиции пользователя в чате для восстановления между сессиями"""
        last_visible_message_id = data.get('last_visible_message_id')
        scroll_position_percent = data.get('scroll_position_percent', 0.0)

        try:
            # Получаем комнату и позицию пользователя
            room, _ = Room.objects.get_or_create(name=self.room_name)
            position = UserChatPosition.get_or_create_for_user(self.user, room)

            # Сохраняем позицию
            if last_visible_message_id:
                position.last_visible_message_id = last_visible_message_id
            position.scroll_position_percent = scroll_position_percent
            position.save()

            logger.info(f"Position saved for {self.user.username} in {self.room_name}: "
                       f"message_id={last_visible_message_id}, scroll={scroll_position_percent:.2f}")

        except Exception as e:
            logger.error(f"Error saving position: {e}")
            self.send_error("Ошибка при сохранении позиции")

    def handle_mark_as_read(self, data):
        """Обработка отметки сообщений как прочитанных"""
        message_id = data.get('message_id')
        up_to_time = data.get('up_to_time')

        try:
            # Получаем комнату и позицию пользователя
            room, _ = Room.objects.get_or_create(name=self.room_name)
            position = UserChatPosition.get_or_create_for_user(self.user, room)

            if message_id:
                # Отмечаем до конкретного сообщения
                try:
                    message = Message.objects.get(id=message_id, room=room, is_deleted=False)
                    position.mark_as_read(up_to_message=message)
                    logger.info(f"User {self.user.username} marked messages as read up to {message_id}")
                except Message.DoesNotExist:
                    self.send_error("Сообщение не найдено")
                    return
            elif up_to_time:
                # Отмечаем до конкретного времени
                position.mark_as_read(up_to_time=timezone.datetime.fromisoformat(up_to_time))
                logger.info(f"User {self.user.username} marked messages as read up to {up_to_time}")
            else:
                # Отмечаем все сообщения как прочитанные
                position.mark_as_read()
                logger.info(f"User {self.user.username} marked all messages as read in {self.room_name}")

            # 🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Обновляем кешированные счетчики перед отправкой
            position.unread_count = position.get_unread_messages_count()
            position.personal_notifications_count = position.get_personal_notifications_count()
            position.save()

            # Отправляем обновленную информацию о непрочитанных
            self.send_unread_info(position)

        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")
            self.send_error("Ошибка при отметке сообщений как прочитанных")

    def get_user_position(self):
        """Получает или создает позицию пользователя в текущей комнате"""
        try:
            room, _ = Room.objects.get_or_create(name=self.room_name)
            return UserChatPosition.get_or_create_for_user(self.user, room)
        except Exception as e:
            logger.error(f"Error getting user position: {e}")
            return None

    def send_unread_info(self, position):
        """Отправляет информацию о непрочитанных сообщениях пользователю"""
        try:
            # 🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Всегда отправляем АКТУАЛЬНЫЕ счетчики, не кешированные!
            actual_unread_count = position.get_unread_messages_count()
            actual_personal_count = position.get_personal_notifications_count()

            first_unread = position.get_first_unread_message()
            first_personal = position.get_first_personal_notification()

            # 🎯 НОВОЕ: Определяем позицию для возвращения в чат
            return_position = position.get_return_position()

            # 🎯 НОВАЯ ЛОГИКА: Для первого визита (last_read_at=None) возвращаем специальную позицию
            if position.last_read_at is None:
                # Первый визит - позиционируем в конец чата
                return_position = {
                    'type': 'first_visit',
                    'message_id': None
                }
                logger.info(f"First visit positioning for {self.user.username} in {self.room_name}")

            self.send(text_data=json.dumps({
                "type": "unread_info",
                "unread_count": actual_unread_count,  # ⚡ ОБЩИЙ СЧЕТЧИК НЕПРОЧИТАННЫХ
                "personal_notifications_count": actual_personal_count,  # ⚡ ПЕРСОНАЛЬНЫЕ УВЕДОМЛЕНИЯ
                "first_unread_message_id": str(first_unread.id) if first_unread else None,
                "first_personal_notification_id": str(first_personal.id) if first_personal else None,
                "return_position": return_position,  # 🎯 ПОЗИЦИЯ ДЛЯ ВОЗВРАЩЕНИЯ
                "last_read_at": position.last_read_at.isoformat() if position.last_read_at else None,
                "last_visit_at": position.last_visit_at.isoformat() if position.last_visit_at else None,
                "is_first_visit": position.last_read_at is None,  # 🎯 НОВОЕ: Флаг первого визита
                # 🎯 НОВЫЕ ПОЛЯ ДЛЯ ВОССТАНОВЛЕНИЯ ПОЗИЦИИ МЕЖДУ СЕССИЯМИ
                "saved_position": {
                    "last_visible_message_id": position.last_visible_message_id,
                    "scroll_position_percent": position.scroll_position_percent
                },
                # 🐛 DEBUG: Добавляем отладочную информацию
                "debug_cached_unread": position.unread_count,
                "debug_actual_unread": actual_unread_count,
                "debug_cached_personal": position.personal_notifications_count,
                "debug_actual_personal": actual_personal_count,
                "debug_is_first_visit": position.last_read_at is None
            }))

            # 🔧 ОБНОВЛЯЕМ КЕШИРОВАННЫЕ СЧЕТЧИКИ ДЛЯ СИНХРОНИЗАЦИИ
            if position.unread_count != actual_unread_count or position.personal_notifications_count != actual_personal_count:
                position.unread_count = actual_unread_count
                position.personal_notifications_count = actual_personal_count
                position.save()
                logger.info(f"Updated cached counters for {self.user.username} in {self.room_name}: "
                           f"unread: {actual_unread_count}, personal: {actual_personal_count}")

        except Exception as e:
            logger.error(f"Error sending unread info: {e}")

    def handle_load_more_messages(self, data):
        """Обработка загрузки дополнительных сообщений"""
        before_message_id = data.get('before_message_id')
        limit = data.get('limit', 50)  # По умолчанию 50 сообщений

        try:
            # Получаем комнату
            room, _ = Room.objects.get_or_create(name=self.room_name)

            # Строим базовый запрос
            query = Message.objects.filter(room=room, is_deleted=False)

            # Если указан ID сообщения, загружаем сообщения ДО него
            if before_message_id:
                try:
                    before_message = Message.objects.get(id=before_message_id, room=room, is_deleted=False)
                    query = query.filter(created_at__lt=before_message.created_at)
                except Message.DoesNotExist:
                    self.send_error("Опорное сообщение не найдено")
                    return

            # Получаем сообщения в обратном порядке и ограничиваем количество
            messages = query.select_related(
                'author', 'parent', 'parent__author'
            ).order_by('-created_at')[:limit]

            # Получаем позицию пользователя для определения прочитанности
            user_position = UserChatPosition.get_or_create_for_user(self.user, room)

            # Конвертируем в JSON (в обратном порядке для правильного отображения)
            messages_data = []
            for msg in reversed(messages):
                message_json = self.message_to_json(msg, is_history=True)

                # Определяем прочитанность
                if user_position.last_read_at:
                    message_json['is_read'] = msg.created_at <= user_position.last_read_at
                else:
                    message_json['is_read'] = True

                # 🎯 НОВОЕ: Отмечаем персональные уведомления
                message_json['is_personal_notification'] = msg.is_personal_notification_for(self.user)

                messages_data.append(message_json)

            # Отправляем дополнительные сообщения
            self.send(text_data=json.dumps({
                "type": "more_messages",
                "messages": messages_data,
                "has_more": len(messages) == limit,  # Есть ли еще сообщения для загрузки
                "before_message_id": before_message_id
            }))

            logger.info(f"Loaded {len(messages_data)} more messages for {self.user.username} in {self.room_name}")

        except Exception as e:
            logger.error(f"Error loading more messages: {e}")
            self.send_error("Ошибка загрузки сообщений")

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

    def send_error(self, message):
        """Отправка сообщения об ошибке клиенту"""
        self.send(text_data=json.dumps({
            "type": "error",
            "message": message
        }))

    def extract_clean_content(self, content):
        """Извлекает основной контент из пересланного сообщения для каскадной пересылки"""
        lines = content.strip().split('\n')

        if len(lines) < 3:
            return content

        # 🎯 КАСКАДНАЯ ЛОГИКА: Ищем пользовательский комментарий ДО секции "Переслано"
        forwarded_section_start = -1

        # Находим где начинается секция "📤 Переслано"
        for i, line in enumerate(lines):
            if line.strip().startswith('📤 Переслано') or line.strip().startswith('Переслано'):
                forwarded_section_start = i
                break

        if forwarded_section_start > 0:
            # Есть пользовательский комментарий ДО секции "Переслано"
            user_comment_lines = lines[:forwarded_section_start]
            user_comment = '\n'.join(user_comment_lines).strip()
            if user_comment:
                return user_comment

        # Если нет пользовательского комментария, возвращаем только основной текст
        # после автора (первую содержательную строку, не цитату)
        if forwarded_section_start >= 0 and forwarded_section_start + 2 < len(lines):
            # Пропускаем строку "📤 Переслано..." и строку с автором
            main_content_start = forwarded_section_start + 2
            if main_content_start < len(lines):
                main_content = lines[main_content_start].strip()
                # Возвращаем только первую строку основного контента
                if main_content and not main_content.startswith('📤'):
                    return main_content

        # Fallback: возвращаем весь контент как есть
        return content

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
            'mentions_me': message.mentions_user(self.user),  # 🎯 НОВОЕ: Упоминания пользователя
            'is_personal_notification': message.is_personal_notification_for(self.user),  # 🎯 НОВОЕ: Персональные уведомления
            'likes_count': message.likes_count,
            'dislikes_count': message.dislikes_count,
            'user_reaction': message.get_user_reaction(self.user),  # 'like', 'dislike' или None
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
            "deleter": event["deleter"]
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
            "message": event["message"],
            "pinner": event["pinner"]
        }))

    def message_unpinned(self, event):
        """Уведомление об откреплении сообщения"""
        self.send(text_data=json.dumps({
            "type": "message_unpinned",
            "message": event["message"],
            "unpinner": event["unpinner"]
        }))

    def reaction_updated(self, event):
        """Уведомление об обновлении реакции"""
        self.send(text_data=json.dumps({
            "type": "reaction_updated",
            "message_id": event["message_id"],
            "reaction_type": event["reaction_type"],
            "user": event["user"],
            "likes_count": event["likes_count"],
            "dislikes_count": event["dislikes_count"]
        }))


class GeneralChatConsumer(BaseChatConsumer):
    """Консьюмер для общего чата"""

    def connect(self):
        """Подключение к общему чату"""
        self.room_name = "general"
        # Теперь вызываем родительский connect, но сначала пропускаем строку с room_name
        super().connect()


class VIPChatConsumer(BaseChatConsumer):
    """Консьюмер для VIP чата"""

    def connect(self):
        """Подключение к VIP чату"""
        self.room_name = "vip"
        # Теперь вызываем родительский connect, но сначала пропускаем строку с room_name
        super().connect()
