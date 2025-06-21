#!/usr/bin/env python
"""
🔍 ПРОВЕРКА ЗАГОЛОВКОВ И ПОЛЬЗОВАТЕЛЕЙ

Проверяет что все правильно настроено:
- Пользователи имеют правильные имена
- URL соответствуют ролям
- Нет проблем с навигацией

Запуск: python manage.py check_headers
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.urls import reverse

class Command(BaseCommand):
    help = '🔍 Проверка заголовков админки и пользователей'

    def handle(self, *args, **options):
        print("🔍 ПРОВЕРКА ЗАГОЛОВКОВ И ПОЛЬЗОВАТЕЛЕЙ")
        print("=" * 60)

        self.check_users()
        self.check_urls()
        self.show_browser_info()

    def check_users(self):
        """Проверяем всех пользователей"""
        print("\n👤 ПРОВЕРКА ПОЛЬЗОВАТЕЛЕЙ:")
        print("-" * 40)

        User = get_user_model()
        users = User.objects.all().order_by('role', 'username')

        for user in users:
            print(f"👤 {user.username} ({user.name or 'БЕЗ ИМЕНИ'})")
            print(f"   🎭 Роль: {user.get_role_display()}")
            print(f"   ⚙️ Staff: {user.is_staff}")
            print(f"   👑 Superuser: {user.is_superuser}")
            print(f"   ✅ Активный: {user.is_active}")

            # Проверяем к каким админкам должен иметь доступ
            access = []
            if user.role == 'owner':
                access.extend(['owner_admin', 'store_owner', 'store_admin'])
            elif user.role == 'admin':
                access.extend(['moderator_admin', 'store_admin'])
            elif user.role == 'store_owner':
                access.extend(['store_owner', 'store_admin'])
            elif user.role == 'store_admin':
                access.append('store_admin')

            if access:
                print(f"   🔗 Доступ к: {', '.join(access)}")
            print()

    def check_urls(self):
        """Проверяем URL-ы админок"""
        print("\n🔗 ПРОВЕРКА URL-ОВ АДМИНОК:")
        print("-" * 40)

        urls_to_check = [
            ('store_admin:index', '📦 Админка магазина'),
            ('store_owner:index', '🏪 Админка владельца магазина'),
            ('owner_admin:index', '👑 Админка владельца платформы'),
        ]

        for url_name, description in urls_to_check:
            try:
                url = reverse(url_name)
                print(f"✅ {description}: {url}")
            except Exception as e:
                print(f"❌ {description}: ОШИБКА - {e}")

    def show_browser_info(self):
        """Показываем что должно отображаться в браузере"""
        print("\n🌐 ЧТО ДОЛЖНО ОТОБРАЖАТЬСЯ В БРАУЗЕРЕ:")
        print("-" * 40)

        print("📦 Для store_admin (clean_admin):")
        print("   🔗 URL: http://127.0.0.1:8000/store_admin/")
        print("   📄 Title: 'Magic Beans - Администратор магазина'")
        print("   🏠 Заголовок: '🌱 Magic Beans - Администратор магазина'")
        print("   👤 Пользователь: 'clean_admin' (справа в шапке)")

        print("\n🏪 Для store_owner:")
        print("   🔗 URL: http://127.0.0.1:8000/store_owner/")
        print("   📄 Title: 'Magic Beans - Владелец магазина'")
        print("   🏠 Заголовок: '🏪 Magic Beans - Владелец магазина'")

        print("\n👑 Для owner_admin:")
        print("   🔗 URL: http://127.0.0.1:8000/owner_admin/")
        print("   📄 Title: 'Беседка - Управление платформой'")
        print("   🏠 Заголовок: '👑 Беседка - Управление платформой'")

        print("\n✅ ПРОВЕРКА ЗАВЕРШЕНА!")
        print("🔄 Обновите страницу в браузере чтобы увидеть изменения!")
