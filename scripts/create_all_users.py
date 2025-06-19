#!/usr/bin/env python3
"""
Скрипт создания всех унифицированных пользователей проекта "Беседка"
Согласно BESEDKA_USER_SYSTEM.md
"""

import os
import sys
import django

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from users.models import User

# Унифицированные пользователи согласно BESEDKA_USER_SYSTEM.md
USERS = [
    {
        'username': 'owner',
        'password': 'owner123secure',
        'email': 'owner@besedka.com',
        'role': 'owner',
        'is_staff': True,
        'is_superuser': True
    },
    {
        'username': 'admin',
        'password': 'admin123secure',
        'email': 'admin@besedka.com',
        'role': 'moderator',
        'is_staff': True,
        'is_superuser': False
    },
    {
        'username': 'store_owner',
        'password': 'storeowner123secure',
        'email': 'store.owner@magicbeans.com',
        'role': 'store_owner',
        'is_staff': True,
        'is_superuser': False
    },
    {
        'username': 'store_admin',
        'password': 'storeadmin123secure',
        'email': 'store.admin@magicbeans.com',
        'role': 'store_admin',
        'is_staff': True,
        'is_superuser': False
    },
    {
        'username': 'test_user',
        'password': 'user123secure',
        'email': 'test.user@besedka.com',
        'role': 'user',
        'is_staff': False,
        'is_superuser': False
    }
]

def create_users():
    """Создать всех унифицированных пользователей"""
    print("🔧 Создание унифицированных пользователей...")

    for user_data in USERS:
        username = user_data['username']

        # Проверяем существует ли пользователь
        if User.objects.filter(username=username).exists():
            print(f"✓ Пользователь '{username}' уже существует")
            continue

        # Создаем пользователя
        user = User.objects.create_user(
            username=username,
            password=user_data['password'],
            email=user_data['email']
        )

        # Устанавливаем роль и статусы
        user.role = user_data['role']
        user.is_staff = user_data['is_staff']
        user.is_superuser = user_data['is_superuser']
        user.save()

        print(f"✅ Создан пользователь '{username}' ({user_data['role']})")

    # Статистика
    total_users = User.objects.count()
    print(f"\n📊 Всего пользователей в системе: {total_users}")

    # Проверяем ключевые роли
    for role in ['owner', 'moderator', 'store_owner', 'store_admin']:
        count = User.objects.filter(role=role).count()
        status = "✅" if count == 1 else "⚠️"
        print(f"{status} Роль '{role}': {count} пользователей")

if __name__ == "__main__":
    create_users()
    print("\n🎉 Создание пользователей завершено!")
