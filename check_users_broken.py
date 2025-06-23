#!/usr/bin/env python
"""
ДИАГНОСТИКА СЛОМАННОЙ СИСТЕМЫ ПОЛЬЗОВАТЕЛЕЙ
"""

import os
import sys
import django

# Настройка Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def diagnose_broken_users():
    """Диагностирует что именно сломано в системе пользователей"""

    print("🚨 ДИАГНОСТИКА СЛОМАННОЙ СИСТЕМЫ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 60)

    # Все пользователи
    users = User.objects.all()
    print(f"📊 ВСЕГО ПОЛЬЗОВАТЕЛЕЙ: {users.count()}")
    print()

    print("📋 ВСЕ ПОЛЬЗОВАТЕЛИ:")
    for user in users:
        print(f"   {user.username}: роль='{user.role}', staff={user.is_staff}, super={user.is_superuser}, active={user.is_active}")
    print()

    # Эталонные пользователи по документации
    expected_users = [
        ('owner', 'owner', True, True),
        ('admin', 'moderator', True, False),
        ('store_owner', 'store_owner', True, False),
        ('store_admin', 'store_admin', True, False),
        ('test_user', 'user', False, False)
    ]

    print("🔍 ПРОВЕРКА ЭТАЛОННЫХ ПОЛЬЗОВАТЕЛЕЙ:")
    problems = []

    for username, expected_role, expected_staff, expected_super in expected_users:
        try:
            user = User.objects.get(username=username)

            # Проверяем корректность
            issues = []
            if user.role != expected_role:
                issues.append(f"роль '{user.role}' != '{expected_role}'")
            if user.is_staff != expected_staff:
                issues.append(f"staff {user.is_staff} != {expected_staff}")
            if user.is_superuser != expected_super:
                issues.append(f"super {user.is_superuser} != {expected_super}")
            if not user.is_active:
                issues.append("НЕ АКТИВЕН")

            if issues:
                print(f"   ❌ {username}: {', '.join(issues)}")
                problems.append(username)
            else:
                print(f"   ✅ {username}: ОК")

        except User.DoesNotExist:
            print(f"   ❌ {username}: НЕ НАЙДЕН")
            problems.append(username)

    print()

    # Проверка паролей (попытка авторизации)
    print("🔑 ПРОВЕРКА ПАРОЛЕЙ:")
    expected_passwords = [
        ('owner', 'owner123secure'),
        ('admin', 'admin123secure'),
        ('store_owner', 'storeowner123secure'),
        ('store_admin', 'storeadmin123secure'),
        ('test_user', 'user123secure')
    ]

    from django.contrib.auth import authenticate

    for username, password in expected_passwords:
        try:
            user = authenticate(username=username, password=password)
            if user:
                print(f"   ✅ {username}: пароль корректен")
            else:
                print(f"   ❌ {username}: пароль НЕ корректен")
                problems.append(f"{username}_password")
        except Exception as e:
            print(f"   ❌ {username}: ошибка проверки пароля - {e}")

    print()

    # Итоговый диагноз
    if problems:
        print("💥 СИСТЕМА ПОЛЬЗОВАТЕЛЕЙ СЛОМАНА!")
        print(f"Проблемы: {', '.join(problems)}")

        # Проверяем наличие лишних пользователей
        extra_users = users.exclude(username__in=[u[0] for u in expected_users])
        if extra_users.exists():
            print(f"🗑️  ЛИШНИЕ ПОЛЬЗОВАТЕЛИ: {[u.username for u in extra_users]}")

        return False
    else:
        print("✅ СИСТЕМА ПОЛЬЗОВАТЕЛЕЙ В ПОРЯДКЕ")
        return True

if __name__ == "__main__":
    diagnose_broken_users()
