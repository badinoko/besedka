import json
import logging
from datetime import datetime
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.paginator import Paginator
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.db import database_sync_to_async

from .models import Room, Message, Thread, DiscussionRoom, GlobalChatRoom, VIPChatRoom, ChatReaction

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseChatConsumer(WebsocketConsumer):
    """Базовый класс для всех чат-консьюмеров"""

    def connect(self):
        """Подключение к WebSocket"""
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            self.close()
            return

        self.accept()
        logger.info(f"User {self.user.username} connected to chat")

    def disconnect(self, close_code):
        """Отключение от WebSocket"""
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )
        logger.info(f"User {self.user.username} disconnected from chat")

    def receive(self, text_data):
        """Получение сообщения от клиента"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')

            if message_type == 'message':
                self.handle_message(data)
            elif message_type == 'typing':
                self.handle_typing(data)
            elif message_type == 'fetch_messages':
                self.handle_fetch_messages(data)
            elif message_type == 'fetch_online_users':
                self.handle_fetch_online_users(data)
            elif message_type == 'reaction':
                self.handle_reaction(data)

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def handle_message(self, data):
        """Обработка обычного сообщения"""
        content = data.get('message', '').strip()
        reply_to_id = data.get('reply_to_id')

        if not content:
            return

        # Создаем сообщение
        message = self.create_message(content, reply_to_id)

        # Отправляем сообщение всем в группе
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': self.message_to_json(message)
            }
        )

    def handle_typing(self, data):
        """Обработка индикатора печати"""
        is_typing = data.get('is_typing', False)

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user': self.user.username,
                'is_typing': is_typing
            }
        )

    def handle_fetch_messages(self, data):
        """Обработка запроса сообщений"""
        page = data.get('page', 1)
        messages = self.get_messages(page)

        self.send(text_data=json.dumps({
            'type': 'messages_history',
            'messages': messages
        }))

    def handle_fetch_online_users(self, data):
        """Обработка запроса онлайн пользователей"""
        online_users = self.get_online_users()

        self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': online_users,
            'count': len(online_users)
        }))

    def handle_reaction(self, data):
        """Обработка реакции на сообщение"""
        reaction = data.get('reaction', '')
        message_id = data.get('message_id', '')

        if not reaction or not message_id:
            return

        try:
            from .models import ChatReaction  # Локальный импорт, чтобы избежать циклов

            message = get_object_or_404(Message, id=message_id)

            # Проверяем, ставил ли пользователь уже реакцию на это сообщение
            existing = ChatReaction.objects.filter(message=message, user=self.user).first()
            if existing:
                # Реакция уже существует ‑ ничего не делаем (реакции безотзывные)
                return

            # Создаем новую реакцию (like / dislike)
            if reaction not in dict(ChatReaction.REACTION_CHOICES):
                return

            ChatReaction.objects.create(message=message, user=self.user, reaction_type=reaction)

            # Подсчитываем новые значения
            likes = message.likes_count()
            dislikes = message.dislikes_count()

            # Рассылаем обновление всем участникам комнаты
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'reaction_update',
                    'message_id': message_id,
                    'likes': likes,
                    'dislikes': dislikes,
                }
            )
        except Exception as e:
            logger.error(f"Error handling reaction: {e}")

    def create_message(self, content, reply_to_id=None):
        """Создание сообщения - переопределяется в наследниках"""
        raise NotImplementedError

    def get_messages(self, page=1):
        """Получение сообщений - переопределяется в наследниках"""
        raise NotImplementedError

    def get_online_users(self):
        """Получение онлайн пользователей - переопределяется в наследниках"""
        return []

    def message_to_json(self, message):
        """Преобразование сообщения в JSON"""
        return {
            'id': message.id,
            'author': message.author.username,
            'author_name': message.author.display_name,
            'author_role': message.author.role if hasattr(message.author, 'role') else 'user',
            'author_role_icon': message.author.get_role_icon if hasattr(message.author, 'get_role_icon') else '👤',
            'author_display_name_with_icon': message.author.display_name_with_icon if hasattr(message.author, 'display_name_with_icon') else f"👤 {message.author.display_name}",
            'content': message.content,
            'created': message.created.isoformat(),
            'is_own': message.author == self.user,
            'likes_count': message.likes_count(),
            'dislikes_count': message.dislikes_count(),
            'reply_to': {
                'id': message.reply_to.id,
                'author_name': message.reply_to.author.display_name if message.reply_to else None,
                'content_snippet': message.reply_to.content[:120] if message.reply_to else None,
            } if message.reply_to else None,
            'is_reply_to_me': bool(message.reply_to and message.reply_to.author == self.user),
        }

    def user_to_json(self, user):
        """Преобразование пользователя в JSON"""
        return {
            'id': user.id,
            'username': user.username,
            'display_name': user.display_name,
            'role': user.role if hasattr(user, 'role') else 'user',
            'role_icon': user.get_role_icon if hasattr(user, 'get_role_icon') else '👤',
            'display_name_with_icon': user.display_name_with_icon if hasattr(user, 'display_name_with_icon') else f"👤 {user.display_name}",
            'is_staff': user.is_staff if hasattr(user, 'is_staff') else False,
            'is_superuser': user.is_superuser if hasattr(user, 'is_superuser') else False,
        }

    # WebSocket event handlers
    def chat_message(self, event):
        """Отправка сообщения клиенту"""
        self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))

    def typing_indicator(self, event):
        """Отправка индикатора печати"""
        if event['user'] != self.user.username:  # Не отправляем себе
            self.send(text_data=json.dumps({
                'type': 'typing',
                'user': event['user'],
                'is_typing': event['is_typing']
            }))

    def user_joined(self, event):
        """Уведомление о подключении пользователя"""
        if event['user']['username'] != self.user.username:  # Не отправляем себе
            self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user': event['user']
            }))

    def user_left(self, event):
        """Уведомление об отключении пользователя"""
        if event['user']['username'] != self.user.username:  # Не отправляем себе
            self.send(text_data=json.dumps({
                'type': 'user_left',
                'user': event['user']
            }))

    def reaction_update(self, event):
        """Отправка клиенту обновленных счетчиков реакции"""
        self.send(text_data=json.dumps({
            'type': 'reaction_update',
            'message_id': event['message_id'],
            'likes': event['likes'],
            'dislikes': event['dislikes'],
        }))


class GeneralChatConsumer(BaseChatConsumer):
    """Консьюмер для общего чата"""

    def connect(self):
        super().connect()
        if self.user.is_authenticated:
            self.room_group_name = 'general_chat'

            # Присоединяемся к группе общего чата
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )

            # Получаем или создаем общий чат
            self.global_chat = GlobalChatRoom.get_or_create_default()
            self.room = self.global_chat.room

            # Подключаем пользователя к комнате
            self.room.connect(self.user)

            # Уведомляем других о подключении пользователя
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user': self.user_to_json(self.user)
                }
            )

    def disconnect(self, close_code):
        """Отключение от общего чата"""
        if hasattr(self, 'room') and self.room:
            self.room.disconnect(self.user)

            # Уведомляем других об отключении пользователя
            if hasattr(self, 'room_group_name'):
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'user_left',
                        'user': self.user_to_json(self.user)
                    }
                )

        super().disconnect(close_code)

    def create_message(self, content, reply_to_id=None):
        """Создание сообщения в общем чате"""
        return Message.objects.create(
            author=self.user,
            room=self.room,
            content=content,
            reply_to_id=reply_to_id
        )

    def get_messages(self, page=1):
        """Получение сообщений общего чата"""
        messages = Message.objects.filter(room=self.room).order_by('-created')
        paginator = Paginator(messages, 20)
        page_obj = paginator.get_page(page)

        return [self.message_to_json(msg) for msg in page_obj.object_list]

    def get_online_users(self):
        """Получение онлайн пользователей общего чата"""
        online_users = self.room.connected_clients.all()
        return [self.user_to_json(user) for user in online_users]


class PrivateChatConsumer(BaseChatConsumer):
    """Консьюмер для приватных чатов"""

    def connect(self):
        super().connect()
        if self.user.is_authenticated:
            self.thread_id = self.scope['url_route']['kwargs']['thread_id']

            try:
                self.thread = get_object_or_404(Thread, id=self.thread_id)

                # Проверяем права доступа
                if self.user not in [self.thread.user1, self.thread.user2]:
                    self.close()
                    return

                self.room = self.thread.room
                self.room_group_name = f'private_chat_{self.thread_id}'

                # Присоединяемся к группе приватного чата
                async_to_sync(self.channel_layer.group_add)(
                    self.room_group_name,
                    self.channel_name
                )

            except Thread.DoesNotExist:
                self.close()

    def create_message(self, content, reply_to_id=None):
        """Создание сообщения в приватном чате"""
        return Message.objects.create(
            author=self.user,
            room=self.room,
            content=content,
            reply_to_id=reply_to_id
        )

    def get_messages(self, page=1):
        """Получение сообщений приватного чата"""
        messages = Message.objects.filter(room=self.room).order_by('-created')
        paginator = Paginator(messages, 20)
        page_obj = paginator.get_page(page)

        return [self.message_to_json(msg) for msg in page_obj.object_list]


class DiscussionChatConsumer(BaseChatConsumer):
    """Консьюмер для групповых обсуждений"""

    def connect(self):
        self.discussion_id = self.scope['url_route']['kwargs']['discussion_id']

        super().connect()

        if self.user.is_authenticated:
            self.room_group_name = f'discussion_{self.discussion_id}'

            # Присоединяемся к группе обсуждения
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )

            # Получаем комнату обсуждения
            try:
                self.discussion_room = DiscussionRoom.objects.get(id=self.discussion_id)
                self.room = self.discussion_room.room

                # Подключаем пользователя к комнате
                self.room.connect(self.user)

                # Уведомляем других о подключении пользователя
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'user_joined',
                        'user': self.user_to_json(self.user)
                    }
                )
            except DiscussionRoom.DoesNotExist:
                self.close()

    def disconnect(self, close_code):
        """Отключение от чата обсуждения"""
        if hasattr(self, 'room') and self.room:
            self.room.disconnect(self.user)

            # Уведомляем других об отключении пользователя
            if hasattr(self, 'room_group_name'):
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'user_left',
                        'user': self.user_to_json(self.user)
                    }
                )

        super().disconnect(close_code)

    def create_message(self, content, reply_to_id=None):
        """Создание сообщения в чате обсуждения"""
        return Message.objects.create(
            author=self.user,
            room=self.room,
            content=content,
            reply_to_id=reply_to_id
        )

    def get_messages(self, page=1):
        """Получение сообщений чата обсуждения"""
        messages = Message.objects.filter(room=self.room).order_by('-created')
        paginator = Paginator(messages, 20)
        page_obj = paginator.get_page(page)

        return [self.message_to_json(msg) for msg in page_obj.object_list]

    def get_online_users(self):
        """Получение онлайн пользователей чата обсуждения"""
        online_users = self.room.connected_clients.all()
        return [self.user_to_json(user) for user in online_users]


class VIPChatConsumer(BaseChatConsumer):
    """Консьюмер для VIP чата"""

    def connect(self):
        # Сначала вызываем родительский метод для инициализации self.user
        super().connect()

        if not self.user.is_authenticated:
            self.close()
            return

        # Проверяем, есть ли у пользователя доступ к VIP чату
        # (можно добавить дополнительную логику проверки VIP статуса)

        self.room_group_name = 'vip_chat'

        # Присоединяемся к группе VIP чата
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        # Получаем или создаем VIP чат
        self.vip_chat = VIPChatRoom.get_or_create_default(created_by=self.user)
        self.room = self.vip_chat.room

        # Подключаем пользователя к комнате
        self.room.connect(self.user)

        # Уведомляем других о подключении пользователя
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user': self.user_to_json(self.user)
            }
        )

    def disconnect(self, close_code):
        """Отключение от VIP чата"""
        if hasattr(self, 'room') and self.room:
            self.room.disconnect(self.user)

            # Уведомляем других об отключении пользователя
            if hasattr(self, 'room_group_name'):
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'user_left',
                        'user': self.user_to_json(self.user)
                    }
                )

        super().disconnect(close_code)

    def create_message(self, content, reply_to_id=None):
        """Создание сообщения в VIP чате"""
        return Message.objects.create(
            author=self.user,
            room=self.room,
            content=content,
            reply_to_id=reply_to_id
        )

    def get_messages(self, page=1):
        """Получение сообщений VIP чата"""
        messages = Message.objects.filter(room=self.room).order_by('-created')
        paginator = Paginator(messages, 20)
        page_obj = paginator.get_page(page)

        return [self.message_to_json(msg) for msg in page_obj.object_list]

    def get_online_users(self):
        """Получение онлайн пользователей VIP чата"""
        online_users = self.room.connected_clients.all()
        return [self.user_to_json(user) for user in online_users]
