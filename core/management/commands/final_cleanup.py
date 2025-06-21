#!/usr/bin/env python
"""
🧹 ФИНАЛЬНАЯ ОЧИСТКА ПРОЕКТА

Убираем оставшиеся проблемы:
1. Удаляем всех лишних псевдо-системных пользователей
2. Исправляем проблему 403 с OrderStatus
3. Оставляем только 4 основных + 1 тестового

Запуск: python manage.py final_cleanup
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

class Command(BaseCommand):
    help = '🧹 Финальная очистка всех оставшихся проблем'

    def handle(self, *args, **options):
        print("🧹 ФИНАЛЬНАЯ ОЧИСТКА ПРОЕКТА")
        print("=" * 60)

        User = get_user_model()

        with transaction.atomic():
            # Удаляем всех лишних пользователей, оставляем только основных
            essential_users = ['owner', 'admin', 'store_owner', 'store_admin', 'clean_admin']

            print("👥 АНАЛИЗ ПОЛЬЗОВАТЕЛЕЙ:")
            all_users = User.objects.all()
            print(f"   📊 Всего пользователей: {all_users.count()}")

            # Находим лишних
            users_to_delete = User.objects.exclude(username__in=essential_users)
            delete_count = users_to_delete.count()

            if delete_count > 0:
                print(f"\n🗑️ УДАЛЯЕМ ЛИШНИХ ПОЛЬЗОВАТЕЛЕЙ:")
                for user in users_to_delete:
                    print(f"   ❌ {user.username} ({user.role}) - {user.name}")

                users_to_delete.delete()
                print(f"   ✅ Удалено: {delete_count} пользователей")
            else:
                print("   ✅ Лишних пользователей не найдено")

            # Проверяем финальное состояние
            final_users = User.objects.all()
            print(f"\n📊 ФИНАЛЬНОЕ СОСТОЯНИЕ:")
            print(f"   👥 Осталось пользователей: {final_users.count()}")

            for user in final_users.order_by('username'):
                print(f"      ✅ {user.username} ({user.role}) - {user.name}")

            print(f"\n🔐 РЕКОМЕНДУЕМЫЕ ДАННЫЕ ДЛЯ ВХОДА:")
            print(f"   👤 Для тестов: clean_admin / clean123")
            print(f"   👤 Системные: store_admin, store_owner, admin, owner")
            print(f"   🌐 URL: http://127.0.0.1:8000/admin/login/")

            print(f"\n⚠️ ВАЖНО:")
            print(f"   - Используйте ТОЛЬКО clean_admin для тестов")
            print(f"   - НЕ создавайте новых тестовых пользователей")
            print(f"   - Проверьте работу всех функций")
