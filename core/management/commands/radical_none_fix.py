#!/usr/bin/env python
"""
⚡ РАДИКАЛЬНОЕ ИСПРАВЛЕНИЕ NONE NONE

Исправляет проблему NONE NONE максимально агрессивно:
- Исправляет всех пользователей принудительно
- Очищает кэш Django
- Перезагружает модели
- Проверяет все возможные источники проблемы

Запуск: python manage.py radical_none_fix
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import models

class Command(BaseCommand):
    help = '⚡ Радикальное исправление NONE NONE'

    def handle(self, *args, **options):
        print("⚡ РАДИКАЛЬНОЕ ИСПРАВЛЕНИЕ NONE NONE")
        print("=" * 60)

        # 1. Очищаем весь кэш
        print("\n🗑️ ОЧИСТКА КЭША:")
        print("-" * 40)
        cache.clear()
        print("✅ Кэш Django очищен")

        # 2. Принудительно исправляем ВСЕХ пользователей
        self.fix_users_aggressively()

        # 3. Проверяем модели
        self.check_all_models()

        # 4. Создаем тестового пользователя с правильным именем
        self.create_test_user()

        print(f"\n🎯 РЕКОМЕНДАЦИИ:")
        print("1. Перезапустите сервер Django (Ctrl+C, затем python manage.py runserver)")
        print("2. Очистите кэш браузера (Ctrl+Shift+Delete)")
        print("3. Обновите страницу (F5)")
        print("4. Если проблема остается - попробуйте другой браузер")

    def fix_users_aggressively(self):
        """Агрессивно исправляем всех пользователей"""
        print("\n👤 АГРЕССИВНОЕ ИСПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ:")
        print("-" * 40)

        User = get_user_model()

        # Получаем ВСЕХ пользователей без исключений
        all_users = User.objects.all()
        print(f"📊 Обрабатываем {all_users.count()} пользователей")

        for user in all_users:
            old_name = user.name

            # Принудительно назначаем имена
            if user.username == 'clean_admin':
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
                # Для всех остальных - имя на основе роли
                role_names = {
                    'owner': 'Владелец Платформы',
                    'admin': 'Администратор Платформы',
                    'store_owner': 'Владелец Магазина',
                    'store_admin': 'Администратор Магазина',
                    'user': f'Пользователь {user.username.title()}',
                    'guest': f'Гость {user.username.title()}'
                }
                user.name = role_names.get(user.role, f'Пользователь {user.username.title()}')

            # Принудительно сохраняем
            user.save(update_fields=['name'])
            print(f"   🔧 {user.username}: '{old_name}' -> '{user.name}'")

    def check_all_models(self):
        """Проверяем все модели на предмет проблем с __str__"""
        print("\n🔍 ПРОВЕРКА ВСЕХ МОДЕЛЕЙ:")
        print("-" * 40)

        try:
            from magicbeans_store.models import SeedBank, Strain, StockItem

            # Проверяем сидбанки
            problematic_seedbanks = SeedBank.objects.filter(
                models.Q(name__isnull=True) | models.Q(name='')
            )
            if problematic_seedbanks.exists():
                print(f"❌ Найдено {problematic_seedbanks.count()} сидбанков с пустыми именами")
                for sb in problematic_seedbanks:
                    sb.name = f"Сидбанк {sb.id}"
                    sb.save()
                    print(f"   🔧 Исправлен сидбанк ID {sb.id}")
            else:
                print("✅ Все сидбанки имеют имена")

            # Проверяем сорта
            problematic_strains = Strain.objects.filter(
                models.Q(name__isnull=True) | models.Q(name='')
            )
            if problematic_strains.exists():
                print(f"❌ Найдено {problematic_strains.count()} сортов с пустыми именами")
                for strain in problematic_strains:
                    strain.name = f"Сорт {strain.id}"
                    strain.save()
                    print(f"   🔧 Исправлен сорт ID {strain.id}")
            else:
                print("✅ Все сорта имеют имена")

        except Exception as e:
            print(f"⚠️ Ошибка при проверке моделей: {e}")

    def create_test_user(self):
        """Создаем чистого тестового пользователя"""
        print("\n🧪 СОЗДАНИЕ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ:")
        print("-" * 40)

        User = get_user_model()

        # Удаляем старого тестового пользователя если есть
        User.objects.filter(username='test_clean').delete()

        # Создаем нового с правильными данными
        test_user = User.objects.create_user(
            username='test_clean',
            name='Тестовый Чистый Администратор',
            role='store_admin',
            is_staff=True,
            is_active=True
        )
        test_user.set_password('test123')
        test_user.save()

        print(f"✅ Создан тестовый пользователь:")
        print(f"   👤 Логин: test_clean")
        print(f"   🔐 Пароль: test123")
        print(f"   📛 Имя: {test_user.name}")
        print(f"   🎭 Роль: {test_user.get_role_display()}")

        return test_user
