#!/usr/bin/env python3
import os
import sys
import django

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from users.models import User

try:
    user = User.objects.get(username='owner')
    print(f"✅ Пользователь найден: {user.username}")
    print(f"   Роль: {user.role}")
    print(f"   is_staff: {user.is_staff}")
    print(f"   is_superuser: {user.is_superuser}")
    print(f"   Пароль 'owner123secure': {user.check_password('owner123secure')}")
    print(f"   Пароль 'owner123': {user.check_password('owner123')}")
except User.DoesNotExist:
    print("❌ Пользователь 'owner' не найден!")
    print("Создание пользователя owner...")
    try:
        user = User.objects.create_user(
            username='owner',
            email='owner@besedka.com',
            password='owner123secure',
            role='owner',
            is_staff=True,
            is_superuser=True
        )
        print(f"✅ Пользователь создан: {user.username}")
    except Exception as e:
        print(f"❌ Ошибка создания: {e}")
