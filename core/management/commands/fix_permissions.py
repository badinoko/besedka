#!/usr/bin/env python
"""
🔐 ИСПРАВЛЕНИЕ ПРАВ ДОСТУПА

Решает проблему 403 ошибок в админке:
1. Создает недостающие Django permissions
2. Назначает права пользователям store_admin роли
3. Исправляет проблемы доступа к моделям

Запуск: python manage.py fix_permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from magicbeans_store.models import (
    SeedBank, Strain, StockItem, Order, OrderStatus,
    Promotion, Coupon, ShippingMethod, PaymentMethod,
    StoreSettings, SalesReport, InventoryReport
)

class Command(BaseCommand):
    help = '🔐 Исправление прав доступа для решения 403 ошибок'

    def handle(self, *args, **options):
        print("🔐 ИСПРАВЛЕНИЕ ПРАВ ДОСТУПА")
        print("=" * 60)

        User = get_user_model()

        # Модели для store_admin
        store_admin_models = [
            SeedBank, Strain, StockItem, OrderStatus
        ]

        # Модели для store_owner
        store_owner_models = [
            User, StoreSettings, SalesReport, InventoryReport,
            PaymentMethod, ShippingMethod, Promotion, Coupon
        ]

        with transaction.atomic():
            # 1. Создаем недостающие permissions
            self.ensure_permissions_exist(store_admin_models)
            self.ensure_permissions_exist(store_owner_models)

            # 2. Назначаем права пользователям store_admin
            self.assign_store_admin_permissions(store_admin_models)

            # 3. Назначаем права пользователям store_owner
            self.assign_store_owner_permissions(store_owner_models)

            print("\n🎉 ВСЕ ПРАВА ДОСТУПА ИСПРАВЛЕНЫ!")
            print("💡 Теперь проверьте доступ к OrderStatus - ошибки 403 не должно быть")

    def ensure_permissions_exist(self, models):
        """Убеждаемся что существуют все необходимые permissions"""
        print("\n🔧 ПРОВЕРКА PERMISSIONS...")

        permissions_created = 0
        for model in models:
            content_type = ContentType.objects.get_for_model(model)

            # Стандартные permissions для каждой модели
            perms = ['add', 'change', 'delete', 'view']

            for perm in perms:
                permission_codename = f'{perm}_{model._meta.model_name}'
                permission_name = f'Can {perm} {model._meta.verbose_name}'

                permission, created = Permission.objects.get_or_create(
                    codename=permission_codename,
                    content_type=content_type,
                    defaults={'name': permission_name}
                )

                if created:
                    permissions_created += 1
                    print(f"   ✅ Создано право: {permission_codename}")

        if permissions_created == 0:
            print("   ✅ Все права уже существуют")
        else:
            print(f"   ✅ Создано прав: {permissions_created}")

    def assign_store_admin_permissions(self, models):
        """Назначаем права всем пользователям с ролью store_admin"""
        print("\n👤 НАЗНАЧЕНИЕ ПРАВ STORE_ADMIN...")

        User = get_user_model()
        store_admins = User.objects.filter(role='store_admin')

        print(f"   📊 Найдено store_admin пользователей: {store_admins.count()}")

        permissions_to_assign = []
        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            for perm in ['add', 'change', 'delete', 'view']:
                permission_codename = f'{perm}_{model._meta.model_name}'
                try:
                    permission = Permission.objects.get(
                        codename=permission_codename,
                        content_type=content_type
                    )
                    permissions_to_assign.append(permission)
                except Permission.DoesNotExist:
                    print(f"   ⚠️ Не найдено право: {permission_codename}")

        for user in store_admins:
            # Убираем все старые права
            user.user_permissions.clear()
            # Назначаем новые права
            user.user_permissions.set(permissions_to_assign)
            user.save()

            print(f"   ✅ Права назначены: {user.username}")

        print(f"   ✅ Назначено прав каждому: {len(permissions_to_assign)}")

    def assign_store_owner_permissions(self, models):
        """Назначаем права всем пользователям с ролью store_owner"""
        print("\n👑 НАЗНАЧЕНИЕ ПРАВ STORE_OWNER...")

        User = get_user_model()
        store_owners = User.objects.filter(role='store_owner')

        print(f"   📊 Найдено store_owner пользователей: {store_owners.count()}")

        # store_owner должен иметь права на свои модели + модели store_admin
        all_models = models + [SeedBank, Strain, StockItem, OrderStatus]

        permissions_to_assign = []
        for model in all_models:
            content_type = ContentType.objects.get_for_model(model)
            for perm in ['add', 'change', 'delete', 'view']:
                permission_codename = f'{perm}_{model._meta.model_name}'
                try:
                    permission = Permission.objects.get(
                        codename=permission_codename,
                        content_type=content_type
                    )
                    permissions_to_assign.append(permission)
                except Permission.DoesNotExist:
                    print(f"   ⚠️ Не найдено право: {permission_codename}")

        for user in store_owners:
            # Убираем все старые права
            user.user_permissions.clear()
            # Назначаем новые права
            user.user_permissions.set(permissions_to_assign)
            user.save()

            print(f"   ✅ Права назначены: {user.username}")

        print(f"   ✅ Назначено прав каждому: {len(permissions_to_assign)}")

    def show_user_permissions(self, username):
        """Показать права конкретного пользователя (для отладки)"""
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            permissions = user.user_permissions.all()

            print(f"\n📋 ПРАВА ПОЛЬЗОВАТЕЛЯ {username}:")
            for perm in permissions:
                print(f"   ✅ {perm.codename} - {perm.name}")

            return permissions.count()
        except User.DoesNotExist:
            print(f"   ❌ Пользователь {username} не найден")
            return 0
