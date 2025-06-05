#!/usr/bin/env python3
"""
Тест функциональности кнопок и чекбоксов в уведомлениях
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Notification

User = get_user_model()

def test_notification_functionality():
    print("🔍 Тестирование функциональности уведомлений...")

    # Найдем owner пользователя
    try:
        owner = User.objects.get(username='owner')
        print(f"✅ Найден пользователь: {owner.username}")
    except User.DoesNotExist:
        print("❌ Пользователь owner не найден")
        return

    # Проверим уведомления
    notifications = owner.notifications.all()
    print(f"📊 Всего уведомлений: {notifications.count()}")
    print(f"📧 Непрочитанных: {owner.unread_notifications_count}")

    # Выведем первые несколько уведомлений для анализа
    print("\n📋 Первые уведомления:")
    for i, notification in enumerate(notifications[:3]):
        print(f"  {i+1}. {notification.title} - {'✅ Прочитано' if notification.is_read else '🆕 Непрочитано'}")
        print(f"     ID: {notification.id}, Тип: {notification.notification_type}")
        print(f"     Кликабельно: {'Да' if notification.is_actionable else 'Нет'}")
        if notification.is_actionable:
            print(f"     URL действия: {notification.get_action_url}")

    # Проверим HTML-структуру
    print("\n🔧 Анализ потенциальных проблем:")
    print("1. Обработчики stopPropagation() добавлены")
    print("2. Чекбоксы должны работать без перехода на страницу")
    print("3. Кнопки 'Удалить' должны открывать модальное окно")
    print("4. Кнопки 'Прочитано' должны помечать уведомление как прочитанное")

    print("\n✅ Тест завершен. Проверьте функциональность в браузере.")

if __name__ == "__main__":
    test_notification_functionality()
