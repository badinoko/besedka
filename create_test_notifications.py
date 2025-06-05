#!/usr/bin/env python3
"""
Создание тестовых уведомлений для проверки функциональности
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Notification

User = get_user_model()

def create_test_notifications():
    print("🔍 Создание тестовых уведомлений...")

    # Найдем owner пользователя
    try:
        owner = User.objects.get(username='owner')
        print(f"✅ Найден пользователь: {owner.username}")
    except User.DoesNotExist:
        print("❌ Пользователь owner не найден")
        return

    # Создаем тестовые уведомления
    test_notifications = [
        {
            'title': 'Новый лайк!',
            'message': 'store_owner лайкнул ваш гроу-лог "test"',
            'notification_type': 'like',
            'is_read': False,
            'action_url': '/growlogs/1/',
        },
        {
            'title': 'Новый комментарий!',
            'message': 'store_owner прокомментировал ваш гроу-лог "test"',
            'notification_type': 'comment',
            'is_read': False,
            'action_url': '/growlogs/1/',
        },
        {
            'title': 'Системное уведомление',
            'message': 'Ваш профиль был обновлен',
            'notification_type': 'system',
            'is_read': True,
            'action_url': None,
        },
        {
            'title': 'Новый заказ',
            'message': 'Ваш заказ #123 был создан',
            'notification_type': 'order',
            'is_read': False,
            'action_url': '/store/orders/123/',
        },
    ]

    created_count = 0
    for notif_data in test_notifications:
        # Используем метод create_notification из модели
        notification = Notification.create_notification(
            recipient=owner,
            notification_type=notif_data['notification_type'],
            title=notif_data['title'],
            message=notif_data['message'],
            sender=None  # Системные уведомления
        )
        created_count += 1
        print(f"✅ Создано уведомление: {notification.title}")

    print(f"\n🎉 Создано {created_count} тестовых уведомлений")
    print(f"📊 Всего уведомлений: {owner.notifications.count()}")
    print(f"📧 Непрочитанных: {owner.unread_notifications_count}")

if __name__ == "__main__":
    create_test_notifications()
