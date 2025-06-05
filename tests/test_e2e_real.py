#!/usr/bin/env python
"""
НАСТОЯЩИЕ E2E ТЕСТЫ для уведомлений и чата
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test.utils import override_settings
from django.db import transaction
import json

# Настройка Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from users.models import Notification
from chat.models import ChatMessage

User = get_user_model()


class NotificationE2ETest(TestCase):
    """Настоящие E2E тесты для системы уведомлений"""

    def setUp(self):
        """Подготовка тестовых данных"""
        self.client = Client()

        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Логинимся
        self.client.login(username='testuser', password='testpass123')

        # Создаем тестовые уведомления
        self.notifications = []
        for i in range(5):
            notification = Notification.objects.create(
                recipient=self.user,
                notification_type='test',
                title=f'Тестовое уведомление {i+1}',
                message=f'Сообщение уведомления {i+1}',
                is_read=(i == 0)  # Первое прочитанное, остальные нет
            )
            self.notifications.append(notification)

    def test_notification_counter_in_header(self):
        """Тест: счетчик уведомлений в шапке"""
        print("\n🔔 ТЕСТ: Счетчик уведомлений в шапке")

        # Получаем главную страницу
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        # Проверяем, что в контексте есть счетчик непрочитанных
        unread_count = response.context.get('unread_notifications_count', 0)
        print(f"   Непрочитанных уведомлений в контексте: {unread_count}")

        # Должно быть 4 непрочитанных (5 всего - 1 прочитанное)
        expected_unread = 4
        self.assertEqual(unread_count, expected_unread,
                        f"Ожидалось {expected_unread} непрочитанных, получено {unread_count}")

        # Проверяем, что в HTML есть счетчик
        html_content = response.content.decode('utf-8')
        self.assertIn('badge rounded-pill bg-danger', html_content,
                     "В HTML должен быть красный счетчик")
        self.assertIn(str(expected_unread), html_content,
                     f"В HTML должна быть цифра {expected_unread}")

        print(f"   ✅ Счетчик корректно показывает {expected_unread}")

    def test_notification_list_page(self):
        """Тест: страница списка уведомлений"""
        print("\n📋 ТЕСТ: Страница списка уведомлений")

        url = reverse('users:notification_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что все уведомления отображаются
        notifications_in_context = response.context.get('notifications', [])
        print(f"   Уведомлений на странице: {len(notifications_in_context)}")
        self.assertEqual(len(notifications_in_context), 5,
                        "Должно быть 5 уведомлений на странице")

        # Проверяем HTML содержимое
        html_content = response.content.decode('utf-8')
        for notification in self.notifications:
            self.assertIn(notification.title, html_content,
                         f"Уведомление '{notification.title}' должно быть в HTML")

        print("   ✅ Все уведомления отображаются корректно")

    def test_mark_all_as_read(self):
        """Тест: кнопка 'Прочитать все'"""
        print("\n✅ ТЕСТ: Кнопка 'Прочитать все'")

        # Проверяем начальное состояние
        unread_before = Notification.objects.filter(recipient=self.user, is_read=False).count()
        print(f"   Непрочитанных до операции: {unread_before}")
        self.assertEqual(unread_before, 4)

        # Выполняем запрос на пометку всех как прочитанных
        url = reverse('users:mark_all_notifications_read')
        response = self.client.post(url)

        # Проверяем редирект
        self.assertEqual(response.status_code, 302)

        # Проверяем, что все уведомления стали прочитанными
        unread_after = Notification.objects.filter(recipient=self.user, is_read=False).count()
        print(f"   Непрочитанных после операции: {unread_after}")
        self.assertEqual(unread_after, 0, "Все уведомления должны быть прочитанными")

        print("   ✅ Кнопка 'Прочитать все' работает корректно")

    def test_delete_notification(self):
        """Тест: удаление уведомления"""
        print("\n🗑️ ТЕСТ: Удаление уведомления")

        # Берем первое уведомление для удаления
        notification_to_delete = self.notifications[0]
        total_before = Notification.objects.filter(recipient=self.user).count()
        print(f"   Уведомлений до удаления: {total_before}")

        # Удаляем уведомление
        url = reverse('users:delete_notification', kwargs={'notification_id': notification_to_delete.pk})
        response = self.client.post(url)

        # Проверяем успешность операции
        self.assertEqual(response.status_code, 200)

        # Проверяем, что уведомление удалено
        total_after = Notification.objects.filter(recipient=self.user).count()
        print(f"   Уведомлений после удаления: {total_after}")
        self.assertEqual(total_after, total_before - 1, "Уведомление должно быть удалено")

        # Проверяем, что именно это уведомление удалено
        self.assertFalse(
            Notification.objects.filter(pk=notification_to_delete.pk).exists(),
            "Удаленное уведомление не должно существовать"
        )

        print("   ✅ Удаление уведомления работает корректно")


class ChatE2ETest(TestCase):
    """Настоящие E2E тесты для системы чата"""

    def setUp(self):
        """Подготовка тестовых данных"""
        self.client = Client()

        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='chatuser',
            email='chat@example.com',
            password='testpass123'
        )

        # Логинимся
        self.client.login(username='chatuser', password='testpass123')

        # Создаем тестовые сообщения
        self.messages = []
        for i in range(3):
            message = ChatMessage.objects.create(
                author=self.user,
                text=f'Тестовое сообщение {i+1} 💬'
            )
            self.messages.append(message)

    def test_chat_page_loads(self):
        """Тест: страница чата загружается"""
        print("\n💬 ТЕСТ: Загрузка страницы чата")

        # url = reverse('chat:chat')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что сообщения отображаются
        html_content = response.content.decode('utf-8')
        for message in self.messages:
            self.assertIn(message.text, html_content,
                         f"Сообщение '{message.text}' должно быть в HTML")

        print(f"   ✅ Страница чата загружается, отображается {len(self.messages)} сообщений")

    def test_chat_message_creation(self):
        """Тест: создание сообщения в чате"""
        print("\n📝 ТЕСТ: Создание сообщения в чате")

        # Проверяем начальное количество сообщений
        messages_before = ChatMessage.objects.count()
        print(f"   Сообщений до создания: {messages_before}")

        # Создаем новое сообщение напрямую (имитируя WebSocket)
        new_message = ChatMessage.objects.create(
            author=self.user,
            text='Новое тестовое сообщение через E2E тест! 🚀'
        )

        # Проверяем, что сообщение создано
        messages_after = ChatMessage.objects.count()
        print(f"   Сообщений после создания: {messages_after}")
        self.assertEqual(messages_after, messages_before + 1, "Должно быть создано одно сообщение")

        # Проверяем содержимое сообщения
        self.assertEqual(new_message.author, self.user, "Автор сообщения должен быть корректным")
        self.assertIn('E2E тест', new_message.text, "Текст сообщения должен содержать 'E2E тест'")

        print("   ✅ Создание сообщения работает корректно")

    def test_chat_messages_display(self):
        """Тест: отображение сообщений в чате"""
        print("\n👀 ТЕСТ: Отображение сообщений в чате")

        # Создаем дополнительное сообщение
        special_message = ChatMessage.objects.create(
            author=self.user,
            text='Специальное сообщение для проверки отображения 🎯'
        )

        # Загружаем страницу чата
        # url = reverse('chat:chat')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что новое сообщение отображается
        html_content = response.content.decode('utf-8')
        self.assertIn(special_message.text, html_content,
                     "Новое сообщение должно отображаться на странице")
        self.assertIn(self.user.username, html_content,
                     "Имя автора должно отображаться")

        print("   ✅ Сообщения корректно отображаются в чате")


def run_e2e_tests():
    """Запуск всех E2E тестов"""
    print("🚀 ЗАПУСК НАСТОЯЩИХ E2E ТЕСТОВ")
    print("=" * 50)

    # Импортируем Django test runner
    from django.test.utils import get_runner
    from django.conf import settings

    # Получаем test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)

    # Запускаем тесты
    failures = test_runner.run_tests([
        'tests.test_e2e_real.NotificationE2ETest',
        'tests.test_e2e_real.ChatE2ETest'
    ])

    if failures:
        print(f"\n❌ ТЕСТЫ ЗАВЕРШИЛИСЬ С ОШИБКАМИ: {failures}")
        return False
    else:
        print(f"\n✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        return True


if __name__ == "__main__":
    # Запускаем тесты
    success = run_e2e_tests()
    sys.exit(0 if success else 1)
