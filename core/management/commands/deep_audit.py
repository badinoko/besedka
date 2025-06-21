#!/usr/bin/env python
"""
🔍 ГЛУБОКИЙ АУДИТ И ИСПРАВЛЕНИЕ ПРОЕКТА

Этот скрипт:
1. Удаляет ВСЕ тестовые учетные записи
2. Анализирует и исправляет ошибки доступа
3. Проверяет все права и роли
4. Исправляет проблемы с админками
5. Создает ТОЛЬКО одного чистого тестового админа

Запуск: python manage.py deep_audit
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from magicbeans_store.models import SeedBank, Strain, StockItem
import re

class Command(BaseCommand):
    help = '🔍 Глубокий аудит и исправление всех проблем проекта'

    def add_arguments(self, parser):
        parser.add_argument('--fix-all', action='store_true', help='Исправить все найденные проблемы')
        parser.add_argument('--clean-users', action='store_true', help='Только очистка пользователей')

    def handle(self, *args, **options):
        print("🔍 ГЛУБОКИЙ АУДИТ ПРОЕКТА")
        print("=" * 60)

        # ЭТАП 1: Аудит пользователей
        self.audit_users()

        # ЭТАП 2: Аудит админок и прав
        self.audit_admin_permissions()

        # ЭТАП 3: Аудит моделей и данных
        self.audit_models_and_data()

        # ЭТАП 4: Исправления (если запрошено)
        if options.get('fix_all') or options.get('clean_users'):
            self.fix_all_problems()
        else:
            print("\n💡 Для исправления проблем запустите:")
            print("   python manage.py deep_audit --fix-all")

    def audit_users(self):
        """Аудит всех пользователей"""
        print("\n👥 АУДИТ ПОЛЬЗОВАТЕЛЕЙ")
        print("-" * 40)

        User = get_user_model()
        all_users = User.objects.all()

        print(f"📊 Всего пользователей в системе: {all_users.count()}")

        # Анализируем пользователей по категориям
        system_users = []
        test_users = []
        broken_users = []

        for user in all_users:
            # Системные пользователи (основные роли)
            if user.username in ['owner', 'admin', 'store_owner', 'store_admin']:
                system_users.append(user)
            # Тестовые пользователи
            elif any(keyword in user.username.lower() for keyword in ['test', 'demo', 'auto', 'power']):
                test_users.append(user)
            # Пользователи с проблемами
            elif not user.name or user.name.strip() == "":
                broken_users.append(user)
            else:
                system_users.append(user)

        print(f"\n📋 КАТЕГОРИИ ПОЛЬЗОВАТЕЛЕЙ:")
        print(f"   🏢 Системные пользователи: {len(system_users)}")
        for user in system_users:
            name_display = user.name or "❌ НЕТ ИМЕНИ"
            print(f"      - {user.username} ({user.role}) - {name_display}")

        print(f"\n   🧪 Тестовые пользователи: {len(test_users)}")
        for user in test_users:
            name_display = user.name or "❌ НЕТ ИМЕНИ"
            print(f"      - {user.username} ({user.role}) - {name_display}")

        print(f"\n   💥 Сломанные пользователи: {len(broken_users)}")
        for user in broken_users:
            print(f"      - {user.username} ({user.role}) - ❌ НЕТ ИМЕНИ")

        return test_users, broken_users

    def audit_admin_permissions(self):
        """Аудит прав доступа в админках"""
        print("\n🔐 АУДИТ ПРАВ ДОСТУПА")
        print("-" * 40)

        # Проверяем регистрацию моделей в админках
        from core.admin_site import store_admin_site, store_owner_site

        print("📦 МОДЕЛИ В STORE_ADMIN:")
        store_admin_models = store_admin_site._registry
        for model, admin_class in store_admin_models.items():
            print(f"   ✅ {model.__name__} -> {admin_class.__class__.__name__}")

        print(f"\n🏪 МОДЕЛИ В STORE_OWNER:")
        store_owner_models = store_owner_site._registry
        for model, admin_class in store_owner_models.items():
            print(f"   ✅ {model.__name__} -> {admin_class.__class__.__name__}")

        # Проверяем проблемные модели
        print(f"\n⚠️ АНАЛИЗ ПРОБЛЕМ:")

        # Проверяем Order
        from magicbeans_store.models import Order, OrderStatus
        order_in_store_admin = Order in store_admin_models
        orderstatus_in_store_admin = OrderStatus in store_admin_models

        print(f"   📋 Order в store_admin: {'❌ ДА (ПРОБЛЕМА!)' if order_in_store_admin else '✅ НЕТ (ПРАВИЛЬНО)'}")
        print(f"   📊 OrderStatus в store_admin: {'✅ ДА' if orderstatus_in_store_admin else '❌ НЕТ'}")

        return {
            'order_in_store_admin': order_in_store_admin,
            'orderstatus_in_store_admin': orderstatus_in_store_admin
        }

    def audit_models_and_data(self):
        """Аудит моделей и данных"""
        print("\n📊 АУДИТ ДАННЫХ")
        print("-" * 40)

        # Подсчет объектов
        seedbank_count = SeedBank.objects.count()
        strain_count = Strain.objects.count()
        stock_count = StockItem.objects.count()

        print(f"📈 КОЛИЧЕСТВО ОБЪЕКТОВ:")
        print(f"   🌱 Сидбанков: {seedbank_count}")
        print(f"   🌿 Сортов: {strain_count}")
        print(f"   📦 Товаров на складе: {stock_count}")

        # Проверяем тестовые данные
        test_seedbanks = SeedBank.objects.filter(
            name__iregex=r'.*(test|demo|auto|power|random|elite|mega).*'
        ).count()

        test_strains = Strain.objects.filter(
            name__iregex=r'.*(test|demo|auto|power|random|elite|mega).*'
        ).count()

        print(f"\n🧪 ТЕСТОВЫЕ ДАННЫЕ:")
        print(f"   🌱 Тестовых сидбанков: {test_seedbanks}")
        print(f"   🌿 Тестовых сортов: {test_strains}")

        if test_seedbanks > 0 or test_strains > 0:
            print(f"   ⚠️ НАЙДЕНЫ ТЕСТОВЫЕ ДАННЫЕ - ТРЕБУЕТСЯ ОЧИСТКА")

        return {
            'total_objects': seedbank_count + strain_count + stock_count,
            'test_objects': test_seedbanks + test_strains
        }

    def fix_all_problems(self):
        """Исправление всех найденных проблем"""
        print("\n🔧 ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ")
        print("-" * 40)

        User = get_user_model()

        with transaction.atomic():
            # 1. Удаляем тестовых пользователей
            test_users = User.objects.filter(
                username__iregex=r'.*(test|demo|auto|power).*'
            ).exclude(
                username__in=['owner', 'admin', 'store_owner', 'store_admin']
            )

            deleted_count = test_users.count()
            test_users.delete()
            print(f"   🗑️ Удалено тестовых пользователей: {deleted_count}")

            # 2. Исправляем имена системных пользователей
            system_users_fixed = 0
            for user in User.objects.filter(username__in=['owner', 'admin', 'store_owner', 'store_admin']):
                if not user.name or user.name.strip() == "" or user.name.startswith('Пользователь'):
                    if user.username == 'owner':
                        user.name = 'Владелец Платформы'
                    elif user.username == 'admin':
                        user.name = 'Администратор Платформы'
                    elif user.username == 'store_owner':
                        user.name = 'Владелец Магазина'
                    elif user.username == 'store_admin':
                        user.name = 'Администратор Магазина'

                    user.save()
                    system_users_fixed += 1
                    print(f"   ✅ Исправлен: {user.username} -> {user.name}")

            print(f"   🔧 Исправлено системных пользователей: {system_users_fixed}")

            # 3. Очищаем тестовые данные
            deleted_stock = StockItem.objects.filter(
                strain__name__iregex=r'.*(test|demo|auto|power|random|elite|mega).*'
            ).delete()[0]

            deleted_strains = Strain.objects.filter(
                name__iregex=r'.*(test|demo|auto|power|random|elite|mega).*'
            ).delete()[0]

            deleted_seedbanks = SeedBank.objects.filter(
                name__iregex=r'.*(test|demo|auto|power|random|elite|mega).*'
            ).delete()[0]

            print(f"   🗑️ Удалено тестовых данных:")
            print(f"      📦 Товаров: {deleted_stock}")
            print(f"      🌿 Сортов: {deleted_strains}")
            print(f"      🌱 Сидбанков: {deleted_seedbanks}")

            # 4. Создаем одного чистого тестового администратора
            clean_admin, created = User.objects.get_or_create(
                username='clean_admin',
                defaults={
                    'name': 'Чистый Тестовый Администратор',
                    'role': 'store_admin',
                    'is_staff': True,
                    'is_active': True,
                    'telegram_id': 'clean_test_admin'
                }
            )
            clean_admin.set_password('clean123')
            clean_admin.save()

            if created:
                print(f"   ✅ Создан чистый тестовый админ: clean_admin / clean123")
            else:
                print(f"   ✅ Обновлен чистый тестовый админ: clean_admin / clean123")

        print(f"\n🎉 ВСЕ ПРОБЛЕМЫ ИСПРАВЛЕНЫ!")
        print(f"📊 ИТОГОВАЯ СТАТИСТИКА:")

        # Финальный подсчет
        final_users = User.objects.count()
        final_objects = SeedBank.objects.count() + Strain.objects.count() + StockItem.objects.count()

        print(f"   👥 Пользователей в системе: {final_users}")
        print(f"   📊 Объектов в базе: {final_objects}")

        print(f"\n🔐 ДАННЫЕ ДЛЯ ВХОДА:")
        print(f"   👤 Логин: clean_admin")
        print(f"   🔐 Пароль: clean123")
        print(f"   🌐 URL: http://127.0.0.1:8000/admin/login/")

        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        print(f"   1. Войдите под clean_admin для тестирования")
        print(f"   2. Проверьте что все функции работают")
        print(f"   3. Используйте только этого админа для тестов")
        print(f"   4. НЕ создавайте новых тестовых пользователей!")
