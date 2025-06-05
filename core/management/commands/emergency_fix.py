#!/usr/bin/env python
"""
🚨 ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ ПРОБЛЕМ

Быстрая диагностика и исправление основных проблем:
- 403 Forbidden ошибки
- NONE NONE в дропдаунах
- Отсутствующие права пользователей
- Проблемы с кэшем

Запуск: python manage.py emergency_fix
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.contrib.sessions.models import Session

class Command(BaseCommand):
    help = '🚨 Экстренное исправление основных проблем'

    def handle(self, *args, **options):
        print("🚨 ЭКСТРЕННАЯ ДИАГНОСТИКА И ИСПРАВЛЕНИЕ")
        print("=" * 60)

        issues_found = []
        issues_fixed = []

        issues_found.extend(self.check_permissions())
        issues_found.extend(self.check_none_none())
        issues_found.extend(self.check_users())

        if issues_found:
            print(f"\n🔧 НАЙДЕНО ПРОБЛЕМ: {len(issues_found)}")
            for issue in issues_found:
                print(f"   ❌ {issue}")

            print(f"\n🔄 ИСПРАВЛЯЕМ ПРОБЛЕМЫ...")
            issues_fixed.extend(self.fix_all_issues())
        else:
            print(f"\n✅ ПРОБЛЕМ НЕ НАЙДЕНО!")

        self.show_summary(issues_found, issues_fixed)

    def check_permissions(self):
        """Проверяем права пользователей"""
        issues = []
        User = get_user_model()

        # Проверяем основных пользователей
        critical_users = ['test_clean', 'clean_admin', 'store_admin']

        for username in critical_users:
            try:
                user = User.objects.get(username=username)
                if user.role == 'store_admin' and user.user_permissions.count() < 10:
                    issues.append(f"У {username} недостаточно прав ({user.user_permissions.count()})")
            except User.DoesNotExist:
                issues.append(f"Пользователь {username} не существует")

        return issues

    def check_none_none(self):
        """Проверяем NONE NONE проблему"""
        issues = []
        User = get_user_model()

        problematic = User.objects.filter(
            name__isnull=True
        ).union(
            User.objects.filter(name__exact='')
        ).union(
            User.objects.filter(name__icontains='none')
        ).union(
            User.objects.filter(name__icontains='null')
        )

        if problematic.exists():
            issues.append(f"NONE NONE проблема у {problematic.count()} пользователей")

        return issues

    def check_users(self):
        """Проверяем состояние пользователей"""
        issues = []
        User = get_user_model()

        # Проверяем активных staff пользователей
        staff_users = User.objects.filter(is_staff=True, is_active=True)
        if staff_users.count() < 2:
            issues.append(f"Слишком мало активных staff пользователей ({staff_users.count()})")

        # Проверяем роли
        admin_users = User.objects.filter(role__in=['store_admin', 'store_owner'])
        if admin_users.count() < 1:
            issues.append("Нет пользователей с ролями администратора магазина")

        return issues

    def fix_all_issues(self):
        """Исправляем все найденные проблемы"""
        fixed = []
        User = get_user_model()

        # 1. Очищаем кэш
        cache.clear()
        Session.objects.all().delete()
        fixed.append("Очищен кэш и сессии")

        # 2. Исправляем NONE NONE
        problematic_users = User.objects.filter(
            name__isnull=True
        ).union(
            User.objects.filter(name__exact='')
        ).union(
            User.objects.filter(name__icontains='none')
        ).union(
            User.objects.filter(name__icontains='null')
        )

        for user in problematic_users:
            if user.username == 'test_clean':
                user.name = 'Тестовый Чистый Администратор'
            elif user.username == 'clean_admin':
                user.name = 'Чистый Тестовый Администратор'
            elif user.username == 'owner':
                user.name = 'Владелец Платформы'
            elif user.username == 'admin':
                user.name = 'Администратор Платформы'
            elif user.username == 'store_admin':
                user.name = 'Администратор Магазина'
            elif user.username == 'store_owner':
                user.name = 'Владелец Магазина'
            else:
                role_map = {
                    'owner': 'Владелец Платформы',
                    'admin': 'Администратор Платформы',
                    'store_owner': 'Владелец Магазина',
                    'store_admin': 'Администратор Магазина',
                    'user': f'Пользователь {user.username.title()}',
                    'guest': f'Гость {user.username.title()}'
                }
                user.name = role_map.get(user.role, f'Пользователь {user.username.title()}')

            user.save(update_fields=['name'])
            fixed.append(f"Исправлено имя пользователя {user.username}")

        # 3. Исправляем права
        critical_users = ['test_clean', 'clean_admin']
        for username in critical_users:
            try:
                user = User.objects.get(username=username)
                if user.role == 'store_admin' and user.user_permissions.count() < 10:
                    self.assign_store_admin_permissions(user)
                    fixed.append(f"Назначены права для {username}")
            except User.DoesNotExist:
                # Создаем критического пользователя
                user = User.objects.create_user(
                    username=username,
                    name='Тестовый Чистый Администратор' if username == 'test_clean' else 'Чистый Тестовый Администратор',
                    role='store_admin',
                    is_staff=True,
                    is_active=True
                )
                user.set_password('test123' if username == 'test_clean' else 'clean123')
                user.save()
                self.assign_store_admin_permissions(user)
                fixed.append(f"Создан пользователь {username}")

        return fixed

    def assign_store_admin_permissions(self, user):
        """Назначаем права администратора магазина"""
        from magicbeans_store.models import SeedBank, Strain, StockItem, Order, OrderItem

        models_list = [SeedBank, Strain, StockItem, Order, OrderItem]

        for model in models_list:
            content_type = ContentType.objects.get_for_model(model)
            permission_codes = ['add', 'change', 'view']
            if model != Order:  # store_admin не удаляет заказы
                permission_codes.append('delete')

            for perm_code in permission_codes:
                try:
                    permission = Permission.objects.get(
                        codename=f"{perm_code}_{content_type.model}",
                        content_type=content_type
                    )
                    user.user_permissions.add(permission)
                except Permission.DoesNotExist:
                    pass

    def show_summary(self, issues_found, issues_fixed):
        """Показываем итоговую сводку"""
        print(f"\n📊 ИТОГОВАЯ СВОДКА:")
        print("-" * 40)

        if issues_found:
            print(f"🔍 Найдено проблем: {len(issues_found)}")
            print(f"🔧 Исправлено: {len(issues_fixed)}")

            if issues_fixed:
                print(f"\n✅ ИСПРАВЛЕНИЯ:")
                for fix in issues_fixed:
                    print(f"   ✅ {fix}")
        else:
            print("✅ Система работает корректно!")

        # Текущее состояние системы
        User = get_user_model()
        print(f"\n📈 ТЕКУЩЕЕ СОСТОЯНИЕ:")
        print(f"   👥 Всего пользователей: {User.objects.count()}")
        print(f"   ⚙️ Staff пользователей: {User.objects.filter(is_staff=True).count()}")
        print(f"   🏪 Администраторов магазина: {User.objects.filter(role='store_admin').count()}")

        # Рекомендации
        print(f"\n🎯 РЕКОМЕНДАЦИИ:")
        if issues_found:
            print("1. Очистите кэш браузера (Ctrl+Shift+Delete)")
            print("2. Обновите страницу (F5)")
            print("3. Войдите заново в систему")
            print("4. Проверьте доступ к админке")
        else:
            print("1. Система работает стабильно")
            print("2. Можно продолжать разработку")

        print(f"\n🔗 ТЕСТОВЫЕ АККАУНТЫ:")
        print("   test_clean / test123")
        print("   clean_admin / clean123")
        print("   URL: http://127.0.0.1:8000/store_admin/")
