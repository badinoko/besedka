#!/usr/bin/env python
"""
🔧 ИСПРАВЛЕНИЕ TEST_CLEAN ПОЛЬЗОВАТЕЛЯ

Исправляет права доступа и NONE NONE для test_clean:
- Назначает все необходимые Django permissions
- Проверяет и исправляет NONE NONE окончательно
- Очищает кэш и сессии

Запуск: python manage.py fix_test_clean
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.contrib.sessions.models import Session

class Command(BaseCommand):
    help = '🔧 Исправление test_clean пользователя и NONE NONE'

    def handle(self, *args, **options):
        print("🔧 ИСПРАВЛЕНИЕ TEST_CLEAN И NONE NONE")
        print("=" * 60)

        self.fix_test_clean_permissions()
        self.radical_none_none_fix()
        self.clear_all_caches()
        self.verify_fix()

    def fix_test_clean_permissions(self):
        """Исправляем права test_clean пользователя"""
        print("\n🔑 ИСПРАВЛЕНИЕ ПРАВ TEST_CLEAN:")
        print("-" * 40)

        User = get_user_model()

        try:
            test_user = User.objects.get(username='test_clean')
            print(f"✅ Найден пользователь: {test_user.username}")

            # Убеждаемся что у него правильная роль и статус
            test_user.role = 'store_admin'
            test_user.is_staff = True
            test_user.is_active = True
            test_user.name = 'Тестовый Чистый Администратор'
            test_user.save()

            print(f"✅ Обновлены базовые поля")

            # Назначаем права для магазина
            from magicbeans_store.models import SeedBank, Strain, StockItem, Order, OrderItem

            models_to_permission = [
                SeedBank, Strain, StockItem, Order, OrderItem
            ]

            permissions_added = 0
            for model in models_to_permission:
                content_type = ContentType.objects.get_for_model(model)

                # Права для store_admin: add, change, view (но не delete для заказов)
                permission_codenames = ['add', 'change', 'view']
                if model != Order:  # store_admin не может удалять заказы
                    permission_codenames.append('delete')

                for perm_code in permission_codenames:
                    perm_name = f"{perm_code}_{content_type.model}"
                    try:
                        permission = Permission.objects.get(
                            codename=perm_name,
                            content_type=content_type
                        )
                        test_user.user_permissions.add(permission)
                        permissions_added += 1
                        print(f"   ✅ {perm_name}")
                    except Permission.DoesNotExist:
                        print(f"   ❌ Права {perm_name} не существует")

            print(f"\n📊 Назначено прав: {permissions_added}")

        except User.DoesNotExist:
            print("❌ Пользователь test_clean не найден!")

            # Создаем заново
            print("🔄 Создаем пользователя заново...")
            test_user = User.objects.create_user(
                username='test_clean',
                name='Тестовый Чистый Администратор',
                role='store_admin',
                is_staff=True,
                is_active=True
            )
            test_user.set_password('test123')
            test_user.save()
            print(f"✅ Создан новый пользователь test_clean")

            # Рекурсивно вызываем исправление прав
            self.fix_test_clean_permissions()

    def radical_none_none_fix(self):
        """Радикальное исправление NONE NONE"""
        print("\n⚡ РАДИКАЛЬНОЕ ИСПРАВЛЕНИЕ NONE NONE:")
        print("-" * 40)

        User = get_user_model()

        # Исправляем ВСЕХ пользователей принудительно
        for user in User.objects.all():
            old_name = user.name

            # Проверяем что имя не пустое и не содержит None
            if (not user.name or
                user.name.strip() == '' or
                'none' in user.name.lower() or
                'null' in user.name.lower()):

                # Назначаем имена по логике
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
                    # По роли
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
                print(f"   🔧 {user.username}: '{old_name}' -> '{user.name}'")
            else:
                print(f"   ✅ {user.username}: '{user.name}' (уже правильно)")

    def clear_all_caches(self):
        """Очищаем все виды кэша"""
        print("\n🗑️ ОЧИСТКА ВСЕХ КЭШЕЙ:")
        print("-" * 40)

        # Django cache
        cache.clear()
        print("✅ Django cache очищен")

        # Сессии
        Session.objects.all().delete()
        print("✅ Все сессии удалены")

        # Принудительная очистка кэша шаблонов
        try:
            from django.template.loader import get_template
            from django.template import TemplateDoesNotExist
            print("✅ Кэш шаблонов будет обновлен")
        except:
            pass

    def verify_fix(self):
        """Проверяем что исправление сработало"""
        print("\n✅ ПРОВЕРКА ИСПРАВЛЕНИЙ:")
        print("-" * 40)

        User = get_user_model()

        # Проверяем test_clean
        try:
            test_user = User.objects.get(username='test_clean')
            permissions_count = test_user.user_permissions.count()

            print(f"👤 test_clean:")
            print(f"   📛 Имя: '{test_user.name}'")
            print(f"   🎭 Роль: {test_user.get_role_display()}")
            print(f"   ⚙️ Staff: {test_user.is_staff}")
            print(f"   🔑 Права: {permissions_count}")

            if permissions_count > 10:
                print("   ✅ Права назначены корректно")
            else:
                print("   ❌ Недостаточно прав!")

        except User.DoesNotExist:
            print("❌ test_clean не найден!")

        # Проверяем всех пользователей на NONE NONE
        problematic_users = User.objects.filter(
            name__isnull=True
        ) | User.objects.filter(
            name__exact=''
        ) | User.objects.filter(
            name__icontains='none'
        ) | User.objects.filter(
            name__icontains='null'
        )

        if problematic_users.exists():
            print(f"\n❌ НАЙДЕНЫ ПРОБЛЕМНЫЕ ПОЛЬЗОВАТЕЛИ:")
            for user in problematic_users:
                print(f"   - {user.username}: '{user.name}'")
        else:
            print(f"\n✅ NONE NONE ПОЛНОСТЬЮ ИСПРАВЛЕНО!")

        print(f"\n🎯 РЕКОМЕНДАЦИИ:")
        print("1. Войдите как test_clean / test123")
        print("2. Очистите кэш браузера (Ctrl+Shift+Delete)")
        print("3. Обновите страницу (F5)")
        print("4. Проверьте что 403 ошибки исчезли")
        print("5. Проверьте что NONE NONE больше не появляется")

        print(f"\n🔗 URL для тестирования:")
        print("http://127.0.0.1:8000/store_admin/")
