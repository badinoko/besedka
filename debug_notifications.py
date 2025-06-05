#!/usr/bin/env python3
"""
Диагностика счетчика уведомлений
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from users.models import User, Notification
from core.context_processors.navigation import get_notifications_count, navigation_context
from django.test import RequestFactory

def main():
    print("🔍 ДИАГНОСТИКА СЧЕТЧИКА УВЕДОМЛЕНИЙ")
    print("=" * 50)

    # Получаем пользователя owner
    try:
        owner = User.objects.get(username='owner')
        print(f"✅ Пользователь найден: {owner.username} (id: {owner.id})")
    except User.DoesNotExist:
        print("❌ Пользователь owner не найден!")
        return

    # Проверяем уведомления в БД
    total_notifications = owner.notifications.count()
    unread_notifications_db = owner.notifications.filter(is_read=False).count()

    print(f"\n📊 ДАННЫЕ ИЗ БД:")
    print(f"  Всего уведомлений: {total_notifications}")
    print(f"  Непрочитанных: {unread_notifications_db}")

    # Проверяем через свойство модели
    unread_from_property = owner.unread_notifications_count
    print(f"\n🏷️  ЧЕРЕЗ СВОЙСТВО МОДЕЛИ:")
    print(f"  unread_notifications_count: {unread_from_property}")

    # Проверяем через context processor
    factory = RequestFactory()
    request = factory.get('/')
    request.user = owner

    context = navigation_context(request)
    unread_from_context = context.get('unread_notifications_count', 'НЕ НАЙДЕНО')

    print(f"\n🔧 ЧЕРЕЗ CONTEXT PROCESSOR:")
    print(f"  unread_notifications_count: {unread_from_context}")

    # Проверяем последние уведомления
    print(f"\n📋 ПОСЛЕДНИЕ 5 УВЕДОМЛЕНИЙ:")
    recent = owner.notifications.all()[:5]
    if recent:
        for i, notification in enumerate(recent, 1):
            print(f"  {i}. {notification.title}")
            print(f"     Прочитано: {notification.is_read}")
            print(f"     Дата: {notification.created_at}")
            print(f"     ID: {notification.id}")
            print()
    else:
        print("  Уведомлений нет")

    # Сравнение результатов
    print(f"\n🔍 СРАВНЕНИЕ РЕЗУЛЬТАТОВ:")
    print(f"  БД (прямой запрос): {unread_notifications_db}")
    print(f"  Свойство модели:    {unread_from_property}")
    print(f"  Context processor:  {unread_from_context}")

    if unread_notifications_db == unread_from_property == unread_from_context:
        print("  ✅ Все источники данных согласованы")
    else:
        print("  ❌ НАЙДЕНО РАСХОЖДЕНИЕ!")

    # Дополнительная диагностика
    print(f"\n🔬 ДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА:")

    # Проверяем есть ли уведомления с is_read=None
    none_read = owner.notifications.filter(is_read__isnull=True).count()
    print(f"  Уведомления с is_read=None: {none_read}")

    # Проверяем типы уведомлений
    notification_types = owner.notifications.values('notification_type').distinct()
    print(f"  Типы уведомлений: {list(notification_types)}")

    print(f"\n" + "=" * 50)
    print("✅ Диагностика завершена!")

if __name__ == '__main__':
    main()
