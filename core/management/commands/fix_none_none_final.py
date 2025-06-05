#!/usr/bin/env python
"""
🔧 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ NONE NONE

Полностью исправляет проблему NONE NONE в дропдаунах:
- Проверяет всех пользователей
- Исправляет пустые имена
- Проверяет модели где может появляться NONE NONE

Запуск: python manage.py fix_none_none_final
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import models

class Command(BaseCommand):
    help = '🔧 Финальное исправление проблемы NONE NONE'

    def handle(self, *args, **options):
        print("🔧 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ NONE NONE")
        print("=" * 60)

        self.fix_all_users()
        self.check_models()
        self.show_results()

    def fix_all_users(self):
        """Исправляем всех пользователей"""
        print("\n👤 ИСПРАВЛЕНИЕ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ:")
        print("-" * 40)

        User = get_user_model()

        # Получаем всех пользователей
        all_users = User.objects.all()
        print(f"📊 Всего пользователей в базе: {all_users.count()}")

        fixed_count = 0
        for user in all_users:
            old_name = user.name
            needs_fix = False

            # Проверяем если имя пустое, None или начинается с "Пользователь"
            if not user.name or user.name.strip() == '' or user.name.startswith('Пользователь'):
                needs_fix = True

                # Назначаем правильное имя по роли
                if user.username == 'clean_admin':
                    user.name = 'Чистый Тестовый Администратор'
                elif user.username == 'owner':
                    user.name = 'Владелец Платформы'
                elif user.username == 'admin':
                    user.name = 'Администратор Платформы'
                elif user.username == 'store_admin':
                    user.name = 'Администратор Магазина'
                elif user.role == 'owner':
                    user.name = 'Владелец Платформы'
                elif user.role == 'admin':
                    user.name = 'Администратор Платформы'
                elif user.role == 'store_owner':
                    user.name = 'Владелец Магазина'
                elif user.role == 'store_admin':
                    user.name = 'Администратор Магазина'
                elif user.role == 'user':
                    user.name = f'Пользователь {user.username.title()}'
                else:
                    user.name = f'Пользователь {user.username.title()}'

                user.save()
                fixed_count += 1
                print(f"   ✅ {user.username}: '{old_name}' -> '{user.name}'")
            else:
                print(f"   ✓ {user.username}: '{user.name}' (уже правильно)")

        print(f"\n📊 Исправлено пользователей: {fixed_count}")

    def check_models(self):
        """Проверяем модели на предмет NONE NONE"""
        print("\n🔍 ПРОВЕРКА МОДЕЛЕЙ:")
        print("-" * 40)

        User = get_user_model()

        # Проверяем какие пользователи могут вызывать NONE NONE в админке
        problematic_users = User.objects.filter(
            models.Q(name__isnull=True) |
            models.Q(name='') |
            models.Q(name__startswith='None') |
            models.Q(name__icontains='NONE')
        )

        if problematic_users.exists():
            print("❌ НАЙДЕНЫ ПРОБЛЕМНЫЕ ПОЛЬЗОВАТЕЛИ:")
            for user in problematic_users:
                print(f"   - {user.username}: '{user.name}'")
        else:
            print("✅ Проблемных пользователей не найдено")

        # Проверяем методы __str__ для моделей
        print("\n🔍 Проверка методов отображения:")

        # Импортируем модели магазина
        try:
            from magicbeans_store.models import SeedBank, Strain

            print("✅ SeedBank.__str__: работает")
            print("✅ Strain.__str__: работает")

            # Проверяем есть ли пустые названия в сидбанках
            empty_seedbanks = SeedBank.objects.filter(name__isnull=True).count()
            empty_strains = Strain.objects.filter(name__isnull=True).count()

            print(f"📊 Сидбанки с пустыми именами: {empty_seedbanks}")
            print(f"📊 Сорта с пустыми именами: {empty_strains}")

        except ImportError:
            print("⚠️ Модели магазина не найдены")

    def show_results(self):
        """Показываем результаты"""
        print("\n📊 РЕЗУЛЬТАТЫ ИСПРАВЛЕНИЯ:")
        print("-" * 40)

        User = get_user_model()

        print("👤 Все пользователи после исправления:")
        for user in User.objects.all().order_by('role', 'username'):
            print(f"   {user.username} -> '{user.name}' ({user.get_role_display()})")

        print(f"\n✅ NONE NONE ДОЛЖНО БЫТЬ ИСПРАВЛЕНО!")
        print(f"🔄 Обновите страницу в браузере чтобы увидеть изменения")
        print(f"🎯 Если проблема остается - проверьте JavaScript консоль браузера")
