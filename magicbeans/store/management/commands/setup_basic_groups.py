from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Command(BaseCommand):
    help = _("Создание базовых групп и прав доступа")

    def handle(self, *args, **options):
        # Создаем группы
        owners_group, created = Group.objects.get_or_create(name="Владельцы")
        if created:
            self.stdout.write(self.style.SUCCESS("Создана группа \"Владельцы\""))
        else:
            self.stdout.write(self.style.WARNING("Группа \"Владельцы\" уже существует"))

        admins_group, created = Group.objects.get_or_create(name="Администраторы")
        if created:
            self.stdout.write(self.style.SUCCESS("Создана группа \"Администраторы\""))
        else:
            self.stdout.write(self.style.WARNING("Группа \"Администраторы\" уже существует"))

        # Импортируем модели здесь, чтобы избежать циклического импорта
        from magicbeans.store.models import (
            Administrator, StockItem, StockMovement,
            Order, OrderItem, SeedBank, Strain, StrainImage
        )

        # Настраиваем права для админов
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
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Добавлено право {perm.codename} для группы Администраторы"
                    )
                )

        for model in admin_model_perms["view_only"]:
            content_type = ContentType.objects.get_for_model(model)
            view_perm = Permission.objects.get(
                content_type=content_type,
                codename=f"view_{model.__name__.lower()}"
            )
            admins_group.permissions.add(view_perm)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Добавлено право просмотра {model.__name__} для группы Администраторы"
                )
            )

        # Добавляем всех суперпользователей в группу владельцев
        for user in User.objects.filter(is_superuser=True):
            user.groups.add(owners_group)
            self.stdout.write(self.style.SUCCESS(f"Пользователь {user.username} добавлен в группу \"Владельцы\""))

        self.stdout.write(self.style.SUCCESS("Базовые группы созданы успешно."))
