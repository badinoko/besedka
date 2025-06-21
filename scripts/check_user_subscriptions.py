#!/usr/bin/env python3
"""
Скрипт для проверки подписок пользователя owner в Rocket.Chat
"""

import os
import sys
from pymongo import MongoClient

def check_user_subscriptions():
    try:
        # Подключение к MongoDB
        client = MongoClient('mongodb://127.0.0.1:27017/')
        db = client['rocketchat']

        print("🔍 ПРОВЕРКА ПОДПИСОК ПОЛЬЗОВАТЕЛЯ 'owner':")
        print("=" * 50)

        # Ищем подписки пользователя owner
        subscriptions = list(db.rocketchat_subscription.find(
            {"u.username": "owner"},
            {"name": 1, "u.username": 1, "rid": 1, "t": 1, "_id": 0}
        ))

        if not subscriptions:
            print("❌ КРИТИЧЕСКАЯ ПРОБЛЕМА: Пользователь 'owner' НЕ ПОДПИСАН НИ НА ОДИН КАНАЛ!")
            print("\n🔧 РЕШЕНИЕ: Необходимо подписать пользователя на каналы")
            return False

        print(f"✅ Найдено подписок: {len(subscriptions)}")
        print("\n📋 СПИСОК ПОДПИСОК:")

        channels_found = []
        for sub in subscriptions:
            channel_name = sub.get('name', 'Unknown')
            channel_type = sub.get('t', 'Unknown')
            rid = sub.get('rid', 'Unknown')

            print(f"  • {channel_name} (тип: {channel_type}, ID: {rid})")
            channels_found.append(channel_name)

        # Проверяем наличие обязательных каналов
        required_channels = ['general', 'GENERAL', 'vip', 'moderators']
        missing_channels = []

        print(f"\n🎯 ПРОВЕРКА ОБЯЗАТЕЛЬНЫХ КАНАЛОВ:")
        for channel in required_channels:
            if channel in channels_found:
                print(f"  ✅ {channel} - ПОДПИСАН")
            else:
                print(f"  ❌ {channel} - НЕ ПОДПИСАН")
                missing_channels.append(channel)

        if missing_channels:
            print(f"\n⚠️ ПРОБЛЕМА: Пользователь НЕ ПОДПИСАН на каналы: {missing_channels}")
            print("🔧 РЕШЕНИЕ: Запустите скрипт подписки на все каналы")
            return False
        else:
            print(f"\n🎉 ОТЛИЧНО: Пользователь подписан на все необходимые каналы!")
            return True

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    result = check_user_subscriptions()
    sys.exit(0 if result else 1)
