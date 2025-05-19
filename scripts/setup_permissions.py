#!/usr/bin/env python
import os
import sys
import django

# Добавляем директорию проекта в путь для импорта модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

# Импорт необходимых модулей после настройки Django
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType

def setup_permissions():
    """Функция для настройки групп и прав доступа"""
    print("Настройка групп и прав доступа")

    # Создание групп пользователей
    owners_group, created = Group.objects.get_or_create(name="Владельцы")
    if created:
        print("Создана группа 'Владельцы'")
    else:
        print("Группа 'Владельцы' уже существует")

    admins_group, created = Group.objects.get_or_create(name="Администраторы")
    if created:
        print("Создана группа 'Администраторы'")
    else:
        print("Группа 'Администраторы' уже существует")

    # Получение всех моделей из приложения store
    from magicbeans.store.models import Administrator
    from magicbeans.store.models import SeedBank, Strain, StrainImage
    from magicbeans.store.models import StockItem, StockMovement
    from magicbeans.store.models import Order, OrderItem, ActionLog

    # Настройка прав для административной группы
    admin_models = {
        # Полный доступ (CRUD)
        'full_access': [StockItem, StockMovement, Order, OrderItem],
        # Только чтение
        'view_only': [SeedBank, Strain, StrainImage, Administrator]
    }

    # Назначаем права для административной группы
    for model in admin_models['full_access']:
        content_type = ContentType.objects.get_for_model(model)
        permissions = Permission.objects.filter(content_type=content_type)

        for perm in permissions:
            admins_group.permissions.add(perm)
            print(f"Добавлено право '{perm.name}' для группы 'Администраторы'")

    # Назначаем права на чтение
    for model in admin_models['view_only']:
        content_type = ContentType.objects.get_for_model(model)
        view_permission = Permission.objects.get(
            content_type=content_type,
            codename=f"view_{model.__name__.lower()}"
        )

        admins_group.permissions.add(view_permission)
        print(f"Добавлено право просмотра '{model.__name__}' для группы 'Администраторы'")

    # Добавляем суперпользователей в группу владельцев
    for user in User.objects.filter(is_superuser=True):
        if user not in owners_group.user_set.all():
            owners_group.user_set.add(user)
            print(f"Пользователь '{user.username}' добавлен в группу 'Владельцы'")

    print("Настройка прав доступа завершена успешно!")

if __name__ == "__main__":
    setup_permissions()
