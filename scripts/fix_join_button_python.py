#!/usr/bin/env python3
"""
Скрипт для исправления проблемы с кнопкой "Join the Channel"
Проблема: у некоторых пользователей пустые роли в подписках на каналы
Решение: исправить роли согласно системе доступа проекта
"""

import pymongo
import sys

def fix_join_channel_issue():
    print("🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ С КНОПКОЙ 'JOIN THE CHANNEL'")
    print("=" * 60)

    try:
        # Подключение к MongoDB
        client = pymongo.MongoClient('mongodb://127.0.0.1:27017/rocketchat')
        db = client.rocketchat

        # Коллекции
        subscriptions = db.rocketchat_subscription
        rooms = db.rocketchat_room

        print("\n📊 ТЕКУЩИЕ ПОДПИСКИ:")
        current_subs = list(subscriptions.find({}, {
            'u': 1,
            'name': 1,
            'roles': 1,
            'joined': 1,
            'autoJoin': 1
        }))

        for sub in current_subs:
            username = sub.get('u', {}).get('username', 'Unknown')
            name = sub.get('name', 'Unknown')
            roles = sub.get('roles', [])
            joined = sub.get('joined', False)
            print(f"Пользователь: {username}, Канал: {name}, Роли: {roles}, Joined: {joined}")

        print("\n🛠️ ИСПРАВЛЕНИЕ РОЛЕЙ:")
        fixes = 0

        # Исправляем подписки пользователя owner
        print("Исправляем пользователя 'owner'...")
        owner_updates = [
            ({'u.username': 'owner', 'name': 'general'},
             {'$set': {'roles': ['owner'], 'joined': True, 'autoJoin': True}}),
            ({'u.username': 'owner', 'name': 'vip'},
             {'$set': {'roles': ['owner', 'vip'], 'joined': True, 'autoJoin': True}}),
            ({'u.username': 'owner', 'name': 'moderators'},
             {'$set': {'roles': ['owner', 'moderator'], 'joined': True, 'autoJoin': True}})
        ]

        owner_modified = 0
        for query, update in owner_updates:
            result = subscriptions.update_one(query, update)
            owner_modified += result.modified_count

        if owner_modified > 0:
            fixes += 1
            print("✅ Роли пользователя 'owner' исправлены")

        # Исправляем подписки пользователя admin (модератор)
        print("Исправляем пользователя 'admin'...")

        # Исправляем роль admin в general (убираем пустые роли)
        admin_general_result = subscriptions.update_one(
            {'u.username': 'admin', 'name': 'general'},
            {'$set': {'roles': ['user'], 'joined': True, 'autoJoin': True}}
        )

        # Исправляем роль admin в moderators
        admin_mod_result = subscriptions.update_one(
            {'u.username': 'admin', 'name': 'moderators'},
            {'$set': {'roles': ['moderator'], 'joined': True, 'autoJoin': True}}
        )

        # Удаляем подписку admin на VIP если есть
        admin_vip_removal = subscriptions.delete_many({'u.username': 'admin', 'name': 'vip'})

        if admin_general_result.modified_count > 0 or admin_mod_result.modified_count > 0 or admin_vip_removal.deleted_count > 0:
            fixes += 1
            print("✅ Роли пользователя 'admin' исправлены")
            if admin_vip_removal.deleted_count > 0:
                print("✅ Убран доступ admin к VIP каналу")

        # Проверяем каналы на настройки autoJoin
        print("\n🔧 ПРОВЕРКА НАСТРОЕК КАНАЛОВ:")
        channels = ['general', 'vip', 'moderators']
        for channel_name in channels:
            channel = rooms.find_one({'name': channel_name})
            if channel:
                update_data = {}
                channel_updated = False

                if not channel.get('autoJoin', False):
                    update_data['autoJoin'] = True
                    channel_updated = True
                if channel.get('joinCodeRequired', False):
                    update_data['joinCodeRequired'] = False
                    channel_updated = True
                if channel.get('broadcast', False):
                    update_data['broadcast'] = False
                    channel_updated = True

                if channel_updated:
                    rooms.update_one({'name': channel_name}, {'$set': update_data})
                    print(f"✅ Канал '{channel_name}' настроен для автоматического присоединения")
                    fixes += 1
                else:
                    print(f"✅ Канал '{channel_name}' уже настроен правильно")

        # Финальная проверка
        print("\n📊 ФИНАЛЬНОЕ СОСТОЯНИЕ ПОДПИСОК:")
        final_subs = list(subscriptions.find({}, {
            'u': 1,
            'name': 1,
            'roles': 1,
            'joined': 1,
            'autoJoin': 1
        }))

        for sub in final_subs:
            username = sub.get('u', {}).get('username', 'Unknown')
            name = sub.get('name', 'Unknown')
            roles = sub.get('roles', [])
            joined = sub.get('joined', False)
            print(f"Пользователь: {username}, Канал: {name}, Роли: {roles}, Joined: {joined}")

        # Резюме
        print("\n" + "=" * 60)
        print(f"🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО! Исправлено {fixes} элементов")
        print("🎯 РЕЗУЛЬТАТ: Кнопка 'Join the Channel' должна исчезнуть")
        print("📝 ЛОГИКА РОЛЕЙ:")
        print("   - owner: все каналы (general, vip, moderators)")
        print("   - admin: общий + модераторы (general, moderators)")
        print("   - user: только общий (general)")
        print("=" * 60)

        client.close()
        return True

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

if __name__ == '__main__':
    success = fix_join_channel_issue()
    sys.exit(0 if success else 1)
