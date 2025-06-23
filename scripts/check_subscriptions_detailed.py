#!/usr/bin/env python3
"""
🔍 ДИАГНОСТИКА ПОДПИСОК MONGODB
Проверка реального состояния подписок пользователя owner
Дата: 23 июня 2025
"""

import pymongo
from datetime import datetime

def check_owner_subscriptions():
    """Детальная проверка подписок owner в MongoDB"""

    print("🚀 ДИАГНОСТИКА ПОДПИСОК ROCKET.CHAT")
    print("="*50)

    try:
        # Подключение к MongoDB
        client = pymongo.MongoClient('mongodb://127.0.0.1:27017/rocketchat?directConnection=true')
        db = client['rocketchat']

        print("✅ Подключение к MongoDB успешно")

        # Поиск пользователя owner
        users_collection = db['rocketchat_users']
        owner_user = users_collection.find_one({'username': 'owner'})

        if not owner_user:
            print("❌ Пользователь owner не найден в базе!")
            return

        owner_id = owner_user['_id']
        print(f"👤 Пользователь owner найден: {owner_id}")

        # Проверка подписок
        subscriptions_collection = db['rocketchat_subscription']
        owner_subscriptions = list(subscriptions_collection.find({'u._id': owner_id}))

        print(f"\n📊 НАЙДЕНО ПОДПИСОК: {len(owner_subscriptions)}")
        print("-"*50)

        if not owner_subscriptions:
            print("❌ НЕТ ПОДПИСОК! Это объясняет кнопку Join Channel!")
            return

        # Детальный анализ каждой подписки
        for i, sub in enumerate(owner_subscriptions, 1):
            print(f"\n🔹 ПОДПИСКА #{i}:")
            print(f"   Канал: {sub.get('name', 'НЕТ ИМЕНИ')}")
            print(f"   Room ID: {sub.get('rid', 'НЕТ ID')}")
            print(f"   Тип: {sub.get('t', 'НЕТ ТИПА')}")
            print(f"   Открыт: {sub.get('open', 'НЕТ СТАТУСА')}")
            print(f"   Роли: {sub.get('roles', [])}")
            print(f"   Активен: {sub.get('active', 'НЕТ СТАТУСА')}")

            # Проверка обязательных полей
            missing_fields = []
            for field in ['name', 'rid', 'open', 'u']:
                if field not in sub:
                    missing_fields.append(field)

            if missing_fields:
                print(f"   ⚠️ ОТСУТСТВУЮТ ПОЛЯ: {missing_fields}")

        # Проверка каналов в базе
        print(f"\n🏠 ПРОВЕРКА КАНАЛОВ В БАЗЕ:")
        print("-"*30)

        rooms_collection = db['rocketchat_room']
        channels = ['general', 'vip', 'moderators']

        for channel in channels:
            room = rooms_collection.find_one({'name': channel})
            if room:
                room_id = room['_id']

                # Есть ли подписка на этот канал?
                has_subscription = any(sub['rid'] == room_id for sub in owner_subscriptions)

                print(f"   📁 {channel}: ID={room_id}, подписка={'✅' if has_subscription else '❌'}")

                if not has_subscription:
                    print(f"      🔴 НЕТ ПОДПИСКИ НА КАНАЛ {channel.upper()}!")
            else:
                print(f"   📁 {channel}: ❌ КАНАЛ НЕ НАЙДЕН В БАЗЕ!")

        # Итоговая диагностика
        print(f"\n🎯 ИТОГОВАЯ ДИАГНОСТИКА:")
        print("="*30)

        expected_channels = {'general', 'vip', 'moderators'}
        subscribed_channels = {sub.get('name') for sub in owner_subscriptions}

        missing_subscriptions = expected_channels - subscribed_channels
        extra_subscriptions = subscribed_channels - expected_channels

        if missing_subscriptions:
            print(f"❌ ОТСУТСТВУЮТ ПОДПИСКИ: {missing_subscriptions}")
            print("   ➤ ЭТО ОБЪЯСНЯЕТ КНОПКУ JOIN CHANNEL!")

        if extra_subscriptions:
            print(f"ℹ️ ДОПОЛНИТЕЛЬНЫЕ ПОДПИСКИ: {extra_subscriptions}")

        if not missing_subscriptions:
            print("✅ ВСЕ ОЖИДАЕМЫЕ ПОДПИСКИ ЕСТЬ")
            print("   ➤ ПРОБЛЕМА НЕ В ПОДПИСКАХ, А В ПРАВАХ ДОСТУПА")

        # Проверка активности подписок
        inactive_subs = [sub for sub in owner_subscriptions if not sub.get('open', True)]
        if inactive_subs:
            print(f"⚠️ НЕАКТИВНЫЕ ПОДПИСКИ: {len(inactive_subs)}")
            for sub in inactive_subs:
                print(f"   └─ {sub.get('name')}: open={sub.get('open')}")

    except Exception as e:
        print(f"💥 ОШИБКА: {e}")

    finally:
        try:
            client.close()
            print("\n🔚 Соединение с MongoDB закрыто")
        except:
            pass

if __name__ == "__main__":
    check_owner_subscriptions()
