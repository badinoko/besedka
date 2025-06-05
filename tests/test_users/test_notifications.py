from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import Notification
from core.notification_service import NotificationService

User = get_user_model()

class NotificationSystemTest(TestCase):
    """Тесты системы уведомлений"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='test_user',
            password='testpass123',
            role='user',
            email='user@test.com'
        )
        cls.admin = User.objects.create_user(
            username='test_admin',
            password='testpass123',
            role='admin',
            email='admin@test.com'
        )

    def setUp(self):
        self.client = Client()

    def test_notification_creation(self):
        """Тест создания уведомления"""
        notification = Notification.objects.create(
            recipient=self.user,
            sender=self.admin,
            notification_type='system',
            title='Тестовое уведомление',
            message='Это тестовое сообщение'
        )

        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.sender, self.admin)
        self.assertEqual(notification.title, 'Тестовое уведомление')
        self.assertFalse(notification.is_read)

    def test_notification_list_view(self):
        """Тест просмотра списка уведомлений"""
        # Создаем уведомление
        Notification.objects.create(
            recipient=self.user,
            notification_type='system',
            title='Тест',
            message='Тестовое сообщение'
        )

        # Логинимся
        self.client.login(username='test_user', password='testpass123')

        # Проверяем доступ к списку уведомлений
        response = self.client.get(reverse('users:notification_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тест')
        self.assertContains(response, 'Тестовое сообщение')

    def test_mark_notification_read(self):
        """Тест пометки уведомления как прочитанного"""
        # Создаем уведомление
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='system',
            title='Тест',
            message='Тестовое сообщение'
        )

        self.assertFalse(notification.is_read)

        # Логинимся
        self.client.login(username='test_user', password='testpass123')

        # Помечаем как прочитанное
        response = self.client.get(
            reverse('users:mark_notification_read', args=[notification.id])
        )

        # Проверяем редирект
        self.assertEqual(response.status_code, 302)

        # Проверяем, что уведомление помечено как прочитанное
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_mark_all_notifications_read(self):
        """Тест пометки всех уведомлений как прочитанных"""
        # Создаем несколько уведомлений
        for i in range(3):
            Notification.objects.create(
                recipient=self.user,
                notification_type='system',
                title=f'Тест {i}',
                message=f'Тестовое сообщение {i}'
            )

        # Проверяем, что все непрочитанные
        self.assertEqual(
            self.user.notifications.filter(is_read=False).count(), 3
        )

        # Логинимся
        self.client.login(username='test_user', password='testpass123')

        # Помечаем все как прочитанные (используем POST вместо GET)
        response = self.client.post(reverse('users:mark_all_notifications_read'))

        # Проверяем редирект
        self.assertEqual(response.status_code, 302)

        # Проверяем, что все уведомления помечены как прочитанные
        self.assertEqual(
            self.user.notifications.filter(is_read=False).count(), 0
        )

    def test_notification_service(self):
        """Тест сервиса уведомлений"""
        # Тест уведомления администраторов
        count = NotificationService.notify_admins(
            title="Тест сервиса",
            message="Тестовое сообщение от сервиса"
        )

        # Проверяем, что уведомление создано для администратора
        self.assertTrue(count > 0)
        admin_notification = self.admin.notifications.filter(
            title="Тест сервиса"
        ).first()
        self.assertIsNotNone(admin_notification)
        self.assertEqual(admin_notification.message, "Тестовое сообщение от сервиса")

    def test_unread_notifications_count(self):
        """Тест подсчета непрочитанных уведомлений"""
        # Создаем уведомления
        for i in range(5):
            Notification.objects.create(
                recipient=self.user,
                notification_type='system',
                title=f'Тест {i}',
                message=f'Сообщение {i}'
            )

        # Проверяем счетчик
        self.assertEqual(self.user.unread_notifications_count, 5)

        # Помечаем одно как прочитанное
        notification = self.user.notifications.first()
        notification.is_read = True
        notification.save()

        # Проверяем обновленный счетчик
        self.assertEqual(self.user.unread_notifications_count, 4)

    def test_notification_type_icon(self):
        """Тест иконок типов уведомлений"""
        notification = Notification.objects.create(
            recipient=self.user,
            notification_type='like',
            title='Лайк',
            message='Вам поставили лайк'
        )

        self.assertEqual(notification.type_icon, '👍')

        notification.notification_type = 'comment'
        self.assertEqual(notification.type_icon, '💬')

        notification.notification_type = 'system'
        self.assertEqual(notification.type_icon, '⚙️')
