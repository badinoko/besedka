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

from .models import Room, Message, Thread, DiscussionRoom, GlobalChatRoom, VIPChatRoom

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

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def handle_message(self, data):
        """Обработка обычного сообщения"""
        content = data.get('message', '').strip()
        if not content:
            return

        # Создаем сообщение
        message = self.create_message(content)

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

    def create_message(self, content):
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
            'author_name': message.author.get_full_name() or message.author.username,
            'content': message.content,
            'created': message.created.isoformat(),
            'is_own': message.author == self.user
        }

    def user_to_json(self, user):
        """Преобразование пользователя в JSON"""
        return {
            'id': user.id,
            'username': user.username,
            'display_name': user.get_full_name() or user.username,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
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

    def create_message(self, content):
        """Создание сообщения в общем чате"""
        return Message.objects.create(
            author=self.user,
            room=self.room,
            content=content
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

    def create_message(self, content):
        """Создание сообщения в приватном чате"""
        return Message.objects.create(
            author=self.user,
            room=self.room,
            content=content
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

    def create_message(self, content):
        """Создание сообщения в чате обсуждения"""
        return Message.objects.create(
            author=self.user,
            room=self.room,
            content=content
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

    def create_message(self, content):
        """Создание сообщения в VIP чате"""
        return Message.objects.create(
            author=self.user,
            room=self.room,
            content=content
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
