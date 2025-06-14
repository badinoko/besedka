#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from gallery.models import Photo
from growlogs.models import GrowLog
from users.models import User
from django.utils import timezone

def create_test_data():
    # Получаем всех пользователей
    users = list(User.objects.all())
    if not users:
        print('Нет пользователей для создания тестовых данных')
        return

    # Создаем тестовые фотографии если их мало
    current_photos = Photo.objects.count()
    print(f'Текущее количество фотографий: {current_photos}')

    if current_photos < 25:
        for i in range(25 - current_photos):
            Photo.objects.create(
                title=f'Тестовое фото {current_photos + i + 1}',
                description=f'Описание тестового фото {current_photos + i + 1}',
                author=users[i % len(users)],
                is_public=True,
                is_active=True
            )
        print(f'Создано {25 - current_photos} новых фотографий')

    # Создаем тестовые гроурепорты если их мало
    current_growlogs = GrowLog.objects.count()
    print(f'Текущее количество гроурепортов: {current_growlogs}')

    if current_growlogs < 25:
        for i in range(25 - current_growlogs):
            GrowLog.objects.create(
                title=f'Тестовый гроурепорт {current_growlogs + i + 1}',
                grower=users[i % len(users)],
                start_date=timezone.now().date(),
                is_public=True,
                is_active=True,
                environment='indoor',
                current_stage='seedling'
            )
        print(f'Создано {25 - current_growlogs} новых гроурепортов')

    print('Итого фотографий:', Photo.objects.count())
    print('Итого гроурепортов:', GrowLog.objects.count())

if __name__ == '__main__':
    create_test_data()
