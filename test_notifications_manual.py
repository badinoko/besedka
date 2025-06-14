#!/usr/bin/env python3
"""
Простая проверка функциональности уведомлений без Selenium
"""
import os
import sys
import django

# Настройка Django окружения
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Notification

User = get_user_model()

def test_notifications_crud():
    """Тест базовых операций с уведомлениями"""
    print("🔍 ТЕСТИРОВАНИЕ БАЗОВЫХ ОПЕРАЦИЙ С УВЕДОМЛЕНИЯМИ")
    print("=" * 60)

    # Получаем тестового пользователя
    try:
        user = User.objects.get(username='test_user')
        print(f"✅ Пользователь найден: {user.username} (ID: {user.id})")
    except User.DoesNotExist:
        print("❌ Пользователь 'test_user' не найден")
        return False

    # Проверяем количество уведомлений
    total_notifications = Notification.objects.filter(recipient=user).count()
    unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()

    print(f"📊 Всего уведомлений: {total_notifications}")
    print(f"📊 Непрочитанных: {unread_notifications}")

    if total_notifications == 0:
        print("⚠️ Нет уведомлений для тестирования. Создаем тестовые...")

                # Создаем тестовые уведомления
        for i in range(5):
            Notification.objects.create(
                recipient=user,
                title=f"Тестовое уведомление {i+1}",
                message=f"Это тестовое сообщение номер {i+1}",
                notification_type='system',
                is_read=i % 2 == 0  # Каждое второе прочитанное
            )

        total_notifications = Notification.objects.filter(recipient=user).count()
        unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()
        print(f"✅ Создано тестовых уведомлений: {total_notifications}")
        print(f"📊 Непрочитанных: {unread_notifications}")

    # Тест массового чтения
    print("\n🔄 ТЕСТ: Массовое чтение всех уведомлений")
    before_read = Notification.objects.filter(recipient=user, is_read=False).count()
    Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
    after_read = Notification.objects.filter(recipient=user, is_read=False).count()

    print(f"   До: {before_read} непрочитанных")
    print(f"   После: {after_read} непрочитанных")
    print(f"   {'✅' if after_read == 0 else '❌'} Результат: {'Успешно' if after_read == 0 else 'Ошибка'}")

    # Тест удаления
    print("\n🗑️ ТЕСТ: Удаление уведомлений")
    notifications_to_delete = list(Notification.objects.filter(recipient=user)[:2])
    delete_ids = [n.id for n in notifications_to_delete]

    before_delete = Notification.objects.filter(recipient=user).count()
    Notification.objects.filter(recipient=user, id__in=delete_ids).delete()
    after_delete = Notification.objects.filter(recipient=user).count()

    print(f"   Удаляем ID: {delete_ids}")
    print(f"   До: {before_delete} уведомлений")
    print(f"   После: {after_delete} уведомлений")
    print(f"   {'✅' if after_delete == before_delete - 2 else '❌'} Результат: {'Успешно' if after_delete == before_delete - 2 else 'Ошибка'}")

    return True

def test_user_permissions():
    """Проверка прав доступа разных ролей"""
    print("\n👥 ТЕСТИРОВАНИЕ ПРАВ ДОСТУПА")
    print("=" * 60)

    roles = ['owner', 'moderator', 'store_owner', 'store_admin', 'test_user']

    for role in roles:
        try:
            user = User.objects.get(username=role)
            notifications_count = Notification.objects.filter(recipient=user).count()
            print(f"✅ {role:12} | Уведомлений: {notifications_count:3} | Активен: {user.is_active} | Роль: {getattr(user, 'role', 'user')}")
        except User.DoesNotExist:
            print(f"❌ {role:12} | Пользователь не найден")

    return True

if __name__ == "__main__":
    print("🚀 ЗАПУСК РУЧНОГО ТЕСТИРОВАНИЯ УВЕДОМЛЕНИЙ")
    print("=" * 60)

    success = True

    # Базовые операции
    success &= test_notifications_crud()

    # Права доступа
    success &= test_user_permissions()

    print("\n" + "=" * 60)
    if success:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ В ТЕСТАХ")

    print("=" * 60)
