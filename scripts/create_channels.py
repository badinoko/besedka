#!/usr/bin/env python3
"""
Скрипт для создания каналов VIP и Moderators в Rocket.Chat
"""

import pymongo
import sys
from datetime import datetime

def connect_to_mongodb():
    """Подключение к MongoDB"""
    try:
        client = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
        db = client["rocketchat"]
        return db
    except Exception as e:
        print(f"❌ Ошибка подключения к MongoDB: {e}")
        return None

def check_existing_channels(db):
    """Проверка существующих каналов"""
    print("=== ПРОВЕРКА СУЩЕСТВУЮЩИХ КАНАЛОВ ===")
    channels = db.rocketchat_room.find({"t": {"$in": ["c", "p"]}})
    for channel in channels:
        channel_type = "PUBLIC" if channel['t'] == 'c' else "PRIVATE"
        print(f"Канал: {channel['name']} ({channel_type})")

def create_channel(db, channel_name, is_private, description):
    """Создание канала"""
    # Проверяем, существует ли канал
    existing = db.rocketchat_room.find_one({"name": channel_name})
    if existing:
        print(f"Канал '{channel_name}' уже существует")
        return existing

    # Генерируем ID для комнаты
    import random
    import string
    room_id = channel_name + ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))

    # Создаем канал
    room = {
        "_id": room_id,
        "name": channel_name,
        "fname": channel_name,
        "t": "p" if is_private else "c",  # 'c' = public channel, 'p' = private group
        "msgs": 0,
        "usersCount": 0,
        "u": {
            "_id": "owner",  # ID владельца
            "username": "owner"
        },
        "ts": datetime.now(),
        "ro": False,  # read-only
        "sysMes": True,
        "_updatedAt": datetime.now(),
        "description": description
    }

    try:
        db.rocketchat_room.insert_one(room)
        print(f"✅ Канал '{channel_name}' создан успешно (ID: {room_id})")

        # Добавляем владельца в подписчики
        sub_id = f"{channel_name}_owner_sub"
        subscription = {
            "_id": sub_id,
            "open": True,
            "alert": True,
            "unread": 0,
            "userMentions": 0,
            "groupMentions": 0,
            "ts": datetime.now(),
            "rid": room_id,
            "name": channel_name,
            "fname": channel_name,
            "t": "p" if is_private else "c",
            "u": {
                "_id": "owner",
                "username": "owner"
            },
            "_updatedAt": datetime.now()
        }

        db.rocketchat_subscription.insert_one(subscription)
        print(f"✅ Подписка для владельца создана (ID: {sub_id})")

        return room
    except Exception as e:
        print(f"❌ Ошибка создания канала '{channel_name}': {e}")
        return None

def setup_auto_join_general(db):
    """Настройка автоматического присоединения к каналу general"""
    print("\n=== НАСТРОЙКА АВТОМАТИЧЕСКОГО ПРИСОЕДИНЕНИЯ К КАНАЛУ GENERAL ===")

    # Находим канал general
    general_room = db.rocketchat_room.find_one({"name": "general"})
    if not general_room:
        print("❌ Канал 'general' не найден!")
        return

    print(f"✅ Канал 'general' найден (ID: {general_room['_id']})")

    # Настройки для автоматического присоединения
    auto_join_settings = [
        {
            "_id": "Accounts_Default_User_Preferences_joinDefaultChannels",
            "value": True,
            "ts": datetime.now(),
            "_updatedAt": datetime.now()
        },
        {
            "_id": "Accounts_Default_User_Preferences_joinDefaultChannelsSilenced",
            "value": False,
            "ts": datetime.now(),
            "_updatedAt": datetime.now()
        }
    ]

    # Применяем настройки
    print("\n=== ПРИМЕНЕНИЕ НАСТРОЕК ===")
    for setting in auto_join_settings:
        try:
            db.rocketchat_settings.replace_one(
                {"_id": setting["_id"]},
                setting,
                upsert=True
            )
            print(f"✅ Настройка '{setting['_id']}' применена")
        except Exception as e:
            print(f"❌ Ошибка применения настройки '{setting['_id']}': {e}")

    # Устанавливаем канал general как канал по умолчанию
    try:
        db.rocketchat_room.update_one(
            {"name": "general"},
            {
                "$set": {
                    "default": True,
                    "featured": True,
                    "broadcast": False
                }
            }
        )
        print("✅ Канал 'general' настроен как канал по умолчанию")
    except Exception as e:
        print(f"❌ Ошибка настройки канала 'general': {e}")

def main():
    """Основная функция"""
    print("🚀 СОЗДАНИЕ КАНАЛОВ ROCKET.CHAT")

    # Подключаемся к MongoDB
    db = connect_to_mongodb()
    if db is None:
        sys.exit(1)

    # Проверяем существующие каналы
    check_existing_channels(db)

    # Создаем новые каналы
    print("\n=== СОЗДАНИЕ НОВЫХ КАНАЛОВ ===")

    # VIP канал (приватный)
    create_channel(db, "vip", True, "VIP чат для премиум пользователей проекта Беседка")

    # Moderators канал (приватный)
    create_channel(db, "moderators", True, "Приватный канал для модераторов и администраторов")

    # Настройка автоматического присоединения
    setup_auto_join_general(db)

    # Финальная проверка
    print("\n=== ФИНАЛЬНАЯ ПРОВЕРКА ===")
    final_channels = list(db.rocketchat_room.find({"t": {"$in": ["c", "p"]}}))
    print(f"Общее количество каналов: {len(final_channels)}")
    for channel in final_channels:
        channel_type = "PUBLIC" if channel['t'] == 'c' else "PRIVATE"
        print(f"Канал: {channel['name']} ({channel_type})")

    print("\n✅ СОЗДАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    main()
