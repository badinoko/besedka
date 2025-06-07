#!/usr/bin/env python3

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from users.models import User, Notification
from gallery.models import Photo
from growlogs.models import GrowLog, GrowLogEntry

def create_notifications():
    """Создать тестовые уведомления"""
    print("🔔 Создание уведомлений...")

    owner = User.objects.get(username='owner')
    test_user = User.objects.get(username='test_user')

    notifications = [
        {'user': owner, 'type': 'system', 'message': 'Добро пожаловать в Беседку!'},
        {'user': test_user, 'type': 'system', 'message': 'Добро пожаловать в Беседку!'},
        {'user': owner, 'type': 'like', 'message': 'Кто-то оценил ваше фото'},
        {'user': test_user, 'type': 'comment', 'message': 'Новый комментарий к вашему гроу-логу'},
    ]

        for notif in notifications:
        Notification.objects.create(
            recipient=notif['user'],
            notification_type=notif['type'],
            title="Новое уведомление",
            message=notif['message']
        )
        print(f"✅ Уведомление для {notif['user'].username}")

def create_growlogs():
    """Создать тестовые гроу-репорты"""
    print("🌱 Создание гроу-репортов...")

    owner = User.objects.get(username='owner')
    test_user = User.objects.get(username='test_user')

    # Первый гроу-лог
    start_date = timezone.now().date() - timedelta(days=20)
    growlog1 = GrowLog.objects.create(
        title='Эксперимент с гидропоникой',
        setup_description='Первый опыт выращивания на гидропонике. Используется система глубоководной культуры.',
        grower=owner,
        start_date=start_date,
        is_public=True
    )
    print(f"✅ Создан гроу-лог: {growlog1.title}")

    # Второй гроу-лог
    start_date2 = timezone.now().date() - timedelta(days=30)
    growlog2 = GrowLog.objects.create(
        title='Автоцветы в домашних условиях',
        setup_description='Компактный гроу с автоцветущими сортами в гроубоксе 60x60.',
        grower=test_user,
        start_date=start_date2,
        is_public=True
    )
    print(f"✅ Создан гроу-лог: {growlog2.title}")

    # Добавляем записи
    for day in [1, 5, 10, 15]:
        GrowLogEntry.objects.create(
            growlog=growlog1,
            day=day,
            activities=f"День {day}: проверка растений, контроль pH и EC.",
            stage='vegetative' if day > 7 else 'seedling'
        )

        GrowLogEntry.objects.create(
            growlog=growlog2,
            day=day,
            activities=f"День {day}: полив, наблюдение за развитием.",
            stage='flowering' if day > 10 else 'vegetative'
        )

def main():
    print("🚀 Создание базовых тестовых данных...")

    try:
        create_notifications()
        create_growlogs()

        print("\n📊 СТАТИСТИКА:")
        print(f"🔔 Уведомлений: {Notification.objects.count()}")
        print(f"🌱 Гроу-логов: {GrowLog.objects.count()}")
        print(f"📝 Записей: {GrowLogEntry.objects.count()}")

        print("\n🎉 Готово!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
