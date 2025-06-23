#!/usr/bin/env python
"""
Создание тестового пользователя для проверки чата
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

def create_test_user():
    """Создать тестового пользователя owner"""

    username = "owner"
    email = "owner@test.com"
    password = "testpass123"

    try:
        with transaction.atomic():
            # Удаляем старого пользователя если есть
            User.objects.filter(username=username).delete()

            # Создаем нового
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='owner',
                is_staff=True,
                is_superuser=True
            )

            print(f"✅ Пользователь {username} создан успешно")
            print(f"📧 Email: {email}")
            print(f"🔑 Пароль: {password}")
            print(f"👑 Роль: {user.role}")
            print(f"🛡️  Staff: {user.is_staff}")

            return user

    except Exception as e:
        print(f"❌ Ошибка создания пользователя: {e}")
        return None

if __name__ == "__main__":
    print("🔧 Создание тестового пользователя...")
    user = create_test_user()

    if user:
        print("\n🎯 ГОТОВО! Теперь можно:")
        print("1. Зайти на http://127.0.0.1:8001/accounts/login/")
        print(f"2. Логин: owner, Пароль: testpass123")
        print("3. Перейти на http://127.0.0.1:8001/chat/integrated/")
        print("4. Проверить работу интегрированного чата")
    else:
        print("💥 Не удалось создать пользователя")
        sys.exit(1)
