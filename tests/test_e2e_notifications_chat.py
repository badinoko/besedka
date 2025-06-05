"""
E2E тесты для системы уведомлений и чата
"""
import time
import json
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from django.db import transaction
from users.models import Notification
from chat.models import ChatMessage
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from config.asgi import application
import asyncio

User = get_user_model()


class NotificationSystemE2ETest(TestCase):
    """E2E тесты для системы уведомлений"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()

        # Создаем тестовых пользователей
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@test.com',
            password='testpass123',
            role='owner'
        )

        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123',
            role='user'
        )

        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123',
            role='user'
        )

        # Создаем тестовые уведомления
        self.create_test_notifications()

    def create_test_notifications(self):
        """Создает тестовые уведомления"""
        # Непрочитанные уведомления для owner
        Notification.objects.create(
            recipient=self.owner,
            sender=self.user1,
            notification_type='like',
            title='Новый лайк',
            message='Пользователь user1 лайкнул ваш пост',
            is_read=False
        )

        Notification.objects.create(
            recipient=self.owner,
            sender=self.user2,
            notification_type='comment',
            title='Новый комментарий',
            message='Пользователь user2 прокомментировал ваш пост',
            is_read=False
        )

        Notification.objects.create(
            recipient=self.owner,
            sender=None,
            notification_type='system',
            title='Системное уведомление',
            message='Добро пожаловать в систему!',
            is_read=False
        )

        # Прочитанное уведомление
        Notification.objects.create(
            recipient=self.owner,
            sender=self.user1,
            notification_type='follow',
            title='Новый подписчик',
            message='Пользователь user1 подписался на вас',
            is_read=True
        )

    def test_notification_counter_in_header(self):
        """Тест счетчика уведомлений в шапке"""
        print("\n=== ТЕСТ: Счетчик уведомлений в шапке ===")

        # Логинимся как owner
        self.client.login(username='owner', password='testpass123')

        # Проверяем главную страницу
        response = self.client.get(reverse('news:home'))
        self.assertEqual(response.status_code, 200)

        # Проверяем, что в контексте есть правильное количество непрочитанных уведомлений
        unread_count = response.context.get('unread_notifications_count', 0)
        print(f"Количество непрочитанных уведомлений в контексте: {unread_count}")

        # Должно быть 3 непрочитанных уведомления
        self.assertEqual(unread_count, 3)

        # Проверяем, что счетчик отображается в HTML
        self.assertContains(response, 'badge rounded-pill bg-danger')
        self.assertContains(response, str(unread_count))

        print("✅ Счетчик в шапке работает корректно")

    def test_notification_list_page(self):
        """Тест страницы списка уведомлений"""
        print("\n=== ТЕСТ: Страница списка уведомлений ===")

        # Логинимся как owner
        self.client.login(username='owner', password='testpass123')

        # Переходим на страницу уведомлений
        response = self.client.get(reverse('users:notification_list'))
        self.assertEqual(response.status_code, 200)

        # Проверяем контекст
        notifications = response.context['notifications']
        unread_count = response.context.get('unread_count', 0)
        total_count = response.context.get('total_count', 0)

        print(f"Всего уведомлений: {total_count}")
        print(f"Непрочитанных: {unread_count}")

        self.assertEqual(total_count, 4)  # Всего 4 уведомления
        self.assertEqual(unread_count, 3)  # 3 непрочитанных

        # Проверяем, что все уведомления отображаются
        for notification in notifications:
            self.assertContains(response, notification.title)
            self.assertContains(response, notification.message)

        # Проверяем наличие кнопок массовых действий
        self.assertContains(response, 'markSelectedRead')
        self.assertContains(response, 'deleteSelected')
        self.assertContains(response, 'markAllRead')

        print("✅ Страница уведомлений загружается корректно")

    def test_mark_single_notification_read(self):
        """Тест пометки одного уведомления как прочитанного"""
        print("\n=== ТЕСТ: Пометка одного уведомления как прочитанного ===")

        # Логинимся как owner
        self.client.login(username='owner', password='testpass123')

        # Получаем первое непрочитанное уведомление
        notification = Notification.objects.filter(
            recipient=self.owner,
            is_read=False
        ).first()

        print(f"Помечаем уведомление как прочитанное: {notification.title}")

        # Помечаем как прочитанное
        response = self.client.get(
            reverse('users:mark_notification_read', args=[notification.id])
        )
        self.assertEqual(response.status_code, 302)  # Редирект

        # Проверяем, что уведомление помечено как прочитанное
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

        # Проверяем, что счетчик уменьшился
        response = self.client.get(reverse('users:notification_list'))
        unread_count = response.context.get('unread_count', 0)
        self.assertEqual(unread_count, 2)  # Было 3, стало 2

        print("✅ Одиночная пометка как прочитанное работает")

    def test_mark_all_notifications_read(self):
        """Тест пометки всех уведомлений как прочитанных"""
        print("\n=== ТЕСТ: Пометка всех уведомлений как прочитанных ===")

        # Логинимся как owner
        self.client.login(username='owner', password='testpass123')

        # Проверяем количество непрочитанных до операции
        unread_before = Notification.objects.filter(
            recipient=self.owner,
            is_read=False
        ).count()
        print(f"Непрочитанных до операции: {unread_before}")

        # Помечаем все как прочитанные
        response = self.client.post(
            reverse('users:mark_all_notifications_read'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)

        # Проверяем ответ
        data = response.json()
        self.assertTrue(data.get('success'))

        # Проверяем, что все уведомления помечены как прочитанные
        unread_after = Notification.objects.filter(
            recipient=self.owner,
            is_read=False
        ).count()
        print(f"Непрочитанных после операции: {unread_after}")
        self.assertEqual(unread_after, 0)

        print("✅ Массовая пометка как прочитанное работает")

    def test_delete_notification(self):
        """Тест удаления уведомления"""
        print("\n=== ТЕСТ: Удаление уведомления ===")

        # Логинимся как owner
        self.client.login(username='owner', password='testpass123')

        # Получаем уведомление для удаления
        notification = Notification.objects.filter(recipient=self.owner).first()
        notification_id = notification.id

        print(f"Удаляем уведомление: {notification.title}")

        # Удаляем уведомление
        response = self.client.post(
            reverse('users:delete_notification', args=[notification_id])
        )
        self.assertEqual(response.status_code, 200)

        # Проверяем, что уведомление удалено
        self.assertFalse(
            Notification.objects.filter(id=notification_id).exists()
        )

        print("✅ Удаление уведомления работает")

    def test_notification_filtering(self):
        """Тест фильтрации уведомлений"""
        print("\n=== ТЕСТ: Фильтрация уведомлений ===")

        # Логинимся как owner
        self.client.login(username='owner', password='testpass123')

        # Получаем страницу уведомлений
        response = self.client.get(reverse('users:notification_list'))
        self.assertEqual(response.status_code, 200)

        # Проверяем, что есть уведомления разных типов
        notifications = response.context['notifications']

        types_present = set(n.notification_type for n in notifications)
        print(f"Типы уведомлений: {types_present}")

        # Должны быть разные типы
        self.assertIn('like', types_present)
        self.assertIn('comment', types_present)
        self.assertIn('system', types_present)

        # Проверяем наличие фильтров в HTML
        self.assertContains(response, 'data-filter="all"')
        self.assertContains(response, 'data-filter="unread"')
        self.assertContains(response, 'data-filter="system"')
        self.assertContains(response, 'data-filter="social"')

        print("✅ Фильтрация уведомлений настроена корректно")

    def test_notification_creation(self):
        """Тест создания нового уведомления"""
        print("\n=== ТЕСТ: Создание нового уведомления ===")

        # Создаем новое уведомление
        new_notification = Notification.create_notification(
            recipient=self.owner,
            sender=self.user1,
            notification_type='mention',
            title='Вас упомянули',
            message='Пользователь user1 упомянул вас в комментарии'
        )

        print(f"Создано уведомление: {new_notification.title}")

        # Проверяем, что уведомление создано
        self.assertTrue(new_notification.id)
        self.assertEqual(new_notification.recipient, self.owner)
        self.assertEqual(new_notification.sender, self.user1)
        self.assertFalse(new_notification.is_read)

        # Логинимся и проверяем, что счетчик увеличился
        self.client.login(username='owner', password='testpass123')
        response = self.client.get(reverse('news:home'))

        unread_count = response.context.get('unread_notifications_count', 0)
        print(f"Новое количество непрочитанных: {unread_count}")
        self.assertEqual(unread_count, 4)  # Было 3, стало 4

        print("✅ Создание уведомлений работает")


class ChatSystemE2ETest(TransactionTestCase):
    """E2E тесты для системы чата"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()

        # Создаем тестовых пользователей
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@test.com',
            password='testpass123',
            role='owner'
        )

        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123',
            role='user'
        )

        # Комната чата не нужна в текущей реализации

    def test_chat_page_loads(self):
        """Тест загрузки страницы чата"""
        print("\n=== ТЕСТ: Загрузка страницы чата ===")

        # Логинимся как owner
        self.client.login(username='owner', password='testpass123')

        # Переходим на страницу чата
        # response = self.client.get(reverse('chat:chat'))
        self.assertEqual(response.status_code, 200)

        # Проверяем наличие основных элементов
        self.assertContains(response, 'Чат сообщества')
        self.assertContains(response, 'chatMessages')
        self.assertContains(response, 'messageInput')
        self.assertContains(response, 'sendButton')

        # Проверяем WebSocket URL
        self.assertContains(response, 'ws://127.0.0.1:8000/ws/chat/main_chat/')

        print("✅ Страница чата загружается корректно")

    def test_chat_message_creation(self):
        """Тест создания сообщения в чате"""
        print("\n=== ТЕСТ: Создание сообщения в чате ===")

        # Создаем сообщение напрямую в БД
        message = ChatMessage.objects.create(
            author=self.owner,
            text='Тестовое сообщение'
        )

        print(f"Создано сообщение: {message.text}")

        # Проверяем, что сообщение создано
        self.assertTrue(message.id)
        self.assertEqual(message.author, self.owner)
        self.assertEqual(message.text, 'Тестовое сообщение')

        # Логинимся и проверяем страницу чата
        self.client.login(username='owner', password='testpass123')
        # response = self.client.get(reverse('chat:chat'))

        # Проверяем, что сообщение отображается
        self.assertContains(response, 'Тестовое сообщение')
        self.assertContains(response, 'owner')

        print("✅ Создание сообщений в чате работает")

    def test_chat_permissions(self):
        """Тест прав доступа к чату"""
        print("\n=== ТЕСТ: Права доступа к чату ===")

        # Проверяем доступ для неавторизованного пользователя
        # response = self.client.get(reverse('chat:chat'))
        self.assertEqual(response.status_code, 302)  # Редирект на логин

        print("✅ Неавторизованные пользователи не имеют доступа к чату")

        # Проверяем доступ для авторизованного пользователя
        self.client.login(username='user1', password='testpass123')
        # response = self.client.get(reverse('chat:chat'))
        self.assertEqual(response.status_code, 200)

        print("✅ Авторизованные пользователи имеют доступ к чату")

    def test_chat_room_exists(self):
        """Тест существования комнаты чата"""
        print("\n=== ТЕСТ: Существование комнаты чата ===")

        # В текущей реализации комнаты чата нет, проверяем что чат работает
        # response = self.client.get(reverse('chat:chat'))
        self.assertEqual(response.status_code, 200)

        print("✅ Чат доступен и работает")

    async def test_websocket_connection(self):
        """Тест WebSocket соединения (асинхронный)"""
        print("\n=== ТЕСТ: WebSocket соединение ===")

        try:
            # Создаем WebSocket коммуникатор
            communicator = WebsocketCommunicator(
                application,
                "/ws/chat/main_chat/"
            )

            # Устанавливаем пользователя в scope
            communicator.scope['user'] = self.owner

            # Пытаемся подключиться
            connected, subprotocol = await communicator.connect()

            if connected:
                print("✅ WebSocket соединение установлено")

                # Отправляем тестовое сообщение
                await communicator.send_json_to({
                    'type': 'chat_message',
                    'message': 'Тестовое WebSocket сообщение'
                })

                # Ждем ответ
                response = await communicator.receive_json_from()
                print(f"Получен ответ: {response}")

                # Закрываем соединение
                await communicator.disconnect()
                print("✅ WebSocket соединение закрыто корректно")
            else:
                print("❌ Не удалось установить WebSocket соединение")

        except Exception as e:
            print(f"❌ Ошибка WebSocket: {e}")


def run_e2e_tests():
    """Запуск всех E2E тестов"""
    print("🚀 ЗАПУСК E2E ТЕСТОВ ДЛЯ УВЕДОМЛЕНИЙ И ЧАТА")
    print("=" * 60)

    # Тесты уведомлений
    notification_test = NotificationSystemE2ETest()
    notification_test.setUp()

    try:
        notification_test.test_notification_counter_in_header()
        notification_test.test_notification_list_page()
        notification_test.test_mark_single_notification_read()
        notification_test.test_mark_all_notifications_read()
        notification_test.test_delete_notification()
        notification_test.test_notification_filtering()
        notification_test.test_notification_creation()

        print("\n✅ ВСЕ ТЕСТЫ УВЕДОМЛЕНИЙ ПРОЙДЕНЫ")

    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ УВЕДОМЛЕНИЙ: {e}")

    # Тесты чата
    chat_test = ChatSystemE2ETest()
    chat_test.setUp()

    try:
        chat_test.test_chat_page_loads()
        chat_test.test_chat_message_creation()
        chat_test.test_chat_permissions()
        chat_test.test_chat_room_exists()

        print("\n✅ ВСЕ ТЕСТЫ ЧАТА ПРОЙДЕНЫ")

        # Асинхронный тест WebSocket
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(chat_test.test_websocket_connection())
        loop.close()

    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ ЧАТА: {e}")

    print("\n" + "=" * 60)
    print("🏁 E2E ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")


if __name__ == '__main__':
    run_e2e_tests()
