#!/usr/bin/env python
"""
ИСПРАВЛЕНИЕ СЛОМАННОЙ СИСТЕМЫ ПОЛЬЗОВАТЕЛЕЙ
"""

import os
import sys
import django

# Настройка Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def fix_broken_users():
    """Исправляет сломанную систему пользователей"""

    print("🔧 ИСПРАВЛЕНИЕ СЛОМАННОЙ СИСТЕМЫ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 60)

    with transaction.atomic():

        # 1. Исправление пароля owner
        try:
            owner = User.objects.get(username='owner')
            owner.set_password('owner123secure')  # ПРАВИЛЬНЫЙ ПАРОЛЬ ПО ДОКУМЕНТАЦИИ
            owner.save()
            print("✅ Пароль owner исправлен на 'owner123secure'")
        except User.DoesNotExist:
            print("❌ Пользователь owner не найден")

        # 2. Удаление лишнего пользователя AnonymousUser
        try:
            anonymous = User.objects.get(username='AnonymousUser')
            anonymous.delete()
            print("✅ Лишний пользователь AnonymousUser удален")
        except User.DoesNotExist:
            print("ℹ️  Пользователь AnonymousUser не найден (уже удален)")

        # 3. Проверка что все эталонные пользователи существуют
        expected_users = [
            ('owner', 'owner', True, True, 'owner123secure'),
            ('admin', 'moderator', True, False, 'admin123secure'),
            ('store_owner', 'store_owner', True, False, 'storeowner123secure'),
            ('store_admin', 'store_admin', True, False, 'storeadmin123secure'),
            ('test_user', 'user', False, False, 'user123secure')
        ]

        for username, role, is_staff, is_superuser, password in expected_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'role': role,
                    'is_staff': is_staff,
                    'is_superuser': is_superuser,
                    'is_active': True,
                    'email': f'{username}@besedka.com'
                }
            )

            if created:
                user.set_password(password)
                user.save()
                print(f"✅ Создан пользователь {username}")
            else:
                # Проверяем и исправляем роль если нужно
                if user.role != role:
                    user.role = role
                    user.is_staff = is_staff
                    user.is_superuser = is_superuser
                    user.save()
                    print(f"✅ Исправлена роль {username}: {role}")

    print("\n🎯 ПРОВЕРКА РЕЗУЛЬТАТА:")

    # Проверяем авторизацию всех пользователей
    from django.contrib.auth import authenticate

    for username, _, _, _, password in expected_users:
        user = authenticate(username=username, password=password)
        if user:
            print(f"   ✅ {username}: авторизация работает")
        else:
            print(f"   ❌ {username}: авторизация НЕ работает")

    print(f"\n📊 Итого пользователей в системе: {User.objects.count()}")

    print("\n🎉 СИСТЕМА ПОЛЬЗОВАТЕЛЕЙ ИСПРАВЛЕНА!")
    print("\n🔑 ПРАВИЛЬНЫЕ УЧЕТНЫЕ ДАННЫЕ:")
    print("   owner / owner123secure")
    print("   admin / admin123secure")
    print("   store_owner / storeowner123secure")
    print("   store_admin / storeadmin123secure")
    print("   test_user / user123secure")

if __name__ == "__main__":
    fix_broken_users()
