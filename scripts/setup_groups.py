# Script para criar grupos e permissões básicas
import os
import sys
import django

# Adiciona o diretório principal ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configura as settings do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

# Importa os módulos necessários
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

# Importando modelos diretamente
from magicbeans.store.models import (
    SeedBank, Strain, StrainImage, StockItem,
    StockMovement, Order, OrderItem, ActionLog
)
from magicbeans.store.models.administrators import Administrator


def setup_groups():
    # Criando grupos
    owners_group, created = Group.objects.get_or_create(name="Владельцы")
    if created:
        print("Создана группа \"Владельцы\"")
    else:
        print("Группа \"Владельцы\" уже существует")

    admins_group, created = Group.objects.get_or_create(name="Администраторы")
    if created:
        print("Создана группа \"Администраторы\"")
    else:
        print("Группа \"Администраторы\" уже существует")

    # Настройка прав для администраторов
    # Список моделей и действий для администраторов
    admin_model_perms = {
        # Модели со всеми правами (CRUD)
        "full_access": [
            StockItem,
            StockMovement,
            Order,
            OrderItem,
        ],
        # Модели только на просмотр
        "view_only": [
            SeedBank,
            Strain,
            StrainImage,
            Administrator,
        ],
    }

    # Добавляем права администраторам
    for model in admin_model_perms["full_access"]:
        content_type = ContentType.objects.get_for_model(model)
        for perm in Permission.objects.filter(content_type=content_type):
            admins_group.permissions.add(perm)
            print(f"Добавлено право {perm.codename} для группы Администраторы")

    for model in admin_model_perms["view_only"]:
        content_type = ContentType.objects.get_for_model(model)
        view_perm = Permission.objects.get(
            content_type=content_type,
            codename=f"view_{model.__name__.lower()}"
        )
        admins_group.permissions.add(view_perm)
        print(f"Добавлено право просмотра {model.__name__} для группы Администраторы")

    # Добавляем всех суперпользователей в группу владельцев
    for user in User.objects.filter(is_superuser=True):
        user.groups.add(owners_group)
        print(f"Пользователь {user.username} добавлен в группу \"Владельцы\"")

    print("Базовые группы созданы успешно.")


if __name__ == "__main__":
    setup_groups()
