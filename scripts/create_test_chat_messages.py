#!/usr/bin/env python3
"""
Скрипт создания тестовых сообщений чата "Беседки"
Создает сообщения от пользователей разных ролей для демонстрации структуры
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from users.models import User
from chat.models import Message, GlobalChatRoom

# Тестовые сообщения от разных ролей
TEST_MESSAGES = [
    {
        'username': 'owner',
        'content': 'Добро пожаловать в чат "Беседки"! Здесь мы обсуждаем все, что касается выращивания растений. Будьте вежливы и помогайте друг другу! 🌱',
        'time_offset': 60  # 60 минут назад
    },
    {
        'username': 'admin',
        'content': 'Напоминаю всем о правилах чата: будьте вежливы и помогайте друг другу! Любые вопросы по модерации направляйте мне в личные сообщения.',
        'time_offset': 50  # 50 минут назад
    },
    {
        'username': 'store_admin',
        'content': 'В магазине появились новые поступления семян! Рекомендую обратить внимание на автоцветы. 🛒',
        'time_offset': 40  # 40 минут назад
    },
    {
        'username': 'test_user',
        'content': 'Спасибо за советы по освещению! Мои растения заметно оживились после смены лампы.',
        'time_offset': 30  # 30 минут назад
    },
    {
        'username': 'test_user',
        'content': 'Кто-нибудь пробовал выращивать томаты в гидропонике? Поделитесь опытом!',
        'time_offset': 20  # 20 минут назад
    },
    {
        'username': 'store_owner',
        'content': 'Не забывайте делиться фотографиями ваших растений в галерее - там можно показать свои лучшие снимки! 📸',
        'time_offset': 10  # 10 минут назад
    }
]

def create_test_messages():
    """Создать тестовые сообщения в общем чате"""
    print("🔧 Создание тестовых сообщений чата...")

    # Получаем общий чат
    try:
        general_chat = GlobalChatRoom.get_or_create_default()
        room = general_chat.room
        print(f"✅ Найден общий чат: {general_chat.name}")
    except Exception as e:
        print(f"❌ Ошибка получения общего чата: {e}")
        return

    # Очищаем старые тестовые сообщения (если есть)
    test_users = User.objects.filter(username__in=[msg['username'] for msg in TEST_MESSAGES])
    old_messages_count = Message.objects.filter(
        room=room,
        author__in=test_users
    ).count()

    if old_messages_count > 0:
        Message.objects.filter(room=room, author__in=test_users).delete()
        print(f"🗑️ Удалено {old_messages_count} старых тестовых сообщений")

    # Создаем новые тестовые сообщения
    created_count = 0

    for msg_data in TEST_MESSAGES:
        try:
            # Получаем пользователя
            user = User.objects.get(username=msg_data['username'])

            # Создаем сообщение с временем в прошлом
            message_time = datetime.now() - timedelta(minutes=msg_data['time_offset'])

            message = Message.objects.create(
                author=user,
                room=room,
                content=msg_data['content'],
                unread=False  # Тестовые сообщения уже "прочитаны"
            )

            # Обновляем время создания
            message.created = message_time
            message.save()

            role_icon = user.get_role_icon() if hasattr(user, 'get_role_icon') else '👤'
            print(f"✅ {role_icon} {user.username}: {msg_data['content'][:50]}...")
            created_count += 1

        except User.DoesNotExist:
            print(f"⚠️ Пользователь '{msg_data['username']}' не найден")
        except Exception as e:
            print(f"❌ Ошибка создания сообщения от {msg_data['username']}: {e}")

    # Статистика
    total_messages = Message.objects.filter(room=room).count()
    print(f"\n📊 Создано новых сообщений: {created_count}")
    print(f"📊 Всего сообщений в общем чате: {total_messages}")

    # Показываем последние сообщения
    recent_messages = Message.objects.filter(room=room).order_by('-created')[:3]
    print(f"\n📝 Последние сообщения:")
    for msg in recent_messages:
        role_icon = msg.author.get_role_icon() if hasattr(msg.author, 'get_role_icon') else '👤'
        print(f"   {role_icon} {msg.author.username}: {msg.content[:50]}...")

if __name__ == "__main__":
    create_test_messages()
    print("\n🎉 Создание тестовых сообщений завершено!")
