from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from magicbeans.store.models import (
    Administrator, SeedBank, Strain, StrainImage, StockItem,
    StockMovement, Order, OrderItem, ActionLog,
)

User = get_user_model()


class Command(BaseCommand):
    help = _('Настройка групп и прав доступа для пользователей магазина')

    def handle(self, *args, **options):
        # Создаем группы
        owners_group, created = Group.objects.get_or_create(name='Владельцы')
        if created:
            self.stdout.write(self.style.SUCCESS(f'Создана группа "Владельцы"'))
        else:
            self.stdout.write(self.style.WARNING(f'Группа "Владельцы" уже существует'))

        admins_group, created = Group.objects.get_or_create(name='Администраторы')
        if created:
            self.stdout.write(self.style.SUCCESS(f'Создана группа "Администраторы"'))
        else:
            self.stdout.write(self.style.WARNING(f'Группа "Администраторы" уже существует'))

        # Очистка существующих прав для групп (если нужно пересоздать права)
        owners_group.permissions.clear()
        admins_group.permissions.clear()

        # Создаем права для владельцев (полный доступ ко всему)
        models = [
            Administrator, SeedBank, Strain, StrainImage,
            StockItem, StockMovement, Order, OrderItem, ActionLog,
            Group, User
        ]

        # Полные права для владельцев
        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=content_type)

            for permission in permissions:
                owners_group.permissions.add(permission)

        self.stdout.write(self.style.SUCCESS(f'Владельцам выданы все права'))

        # Права для администраторов (только работа со складом и заказами)
        admin_models = [StockItem, StockMovement, Order, OrderItem]
        admin_view_only = [SeedBank, Strain, StrainImage]

        # Полные права на работу со складом и заказами
        for model in admin_models:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=content_type)

            for permission in permissions:
                admins_group.permissions.add(permission)

        # Права только на просмотр для некоторых моделей
        for model in admin_view_only:
            content_type = ContentType.objects.get_for_model(model)
            view_permission = Permission.objects.get(
                content_type=content_type,
                codename=f'view_{model.__name__.lower()}'
            )
            admins_group.permissions.add(view_permission)

        self.stdout.write(self.style.SUCCESS(f'Администраторам выданы права на работу со складом'))

        # Привязка существующих суперпользователей к группе владельцев
        for user in User.objects.filter(is_superuser=True):
            user.groups.add(owners_group)
            self.stdout.write(self.style.SUCCESS(f'Пользователь {user.username} добавлен в группу "Владельцы"'))
