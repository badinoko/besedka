#!/usr/bin/env python3
"""
Упрощенный скрипт для создания каналов #vip и #admin в Rocket.Chat
"""
import subprocess
import json

def execute_mongo_command(command):
    """Выполняет команду в MongoDB через Docker"""
    cmd = [
        'docker', 'exec', '-i', 'magic_beans_new-mongo-1',
        'mongosh', 'rocketchat', '--eval', command
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout if result.stdout else "", result.stderr if result.stderr else ""
    except Exception as e:
        return False, "", str(e)

def create_vip_channel():
    """Создает VIP канал"""
    print("📢 Создание VIP канала...")

    command = '''
    db.rocketchat_room.insertOne({
        "_id": "vip_room_2025",
        "name": "vip",
        "fname": "vip",
        "t": "p",
        "description": "VIP чат для привилегированных пользователей",
        "topic": "Эксклюзивный VIP чат 💎",
        "ts": new Date(),
        "ro": false,
        "default": false,
        "sysMes": true,
        "usernames": [],
        "msgs": 0,
        "usersCount": 0,
        "lm": new Date(),
        "_updatedAt": new Date()
    })
    '''

    success, stdout, stderr = execute_mongo_command(command)

    if success:
        print("✅ VIP канал создан!")
        return True
    else:
        print(f"❌ Ошибка создания VIP канала: {stderr}")
        return False

def create_admin_channel():
    """Создает admin канал"""
    print("📢 Создание admin канала...")

    command = '''
    db.rocketchat_room.insertOne({
        "_id": "admin_room_2025",
        "name": "admin",
        "fname": "admin",
        "t": "p",
        "description": "Административный чат для модераторов и владельцев",
        "topic": "Служебный канал для администрации 🛡️",
        "ts": new Date(),
        "ro": false,
        "default": false,
        "sysMes": true,
        "usernames": [],
        "msgs": 0,
        "usersCount": 0,
        "lm": new Date(),
        "_updatedAt": new Date()
    })
    '''

    success, stdout, stderr = execute_mongo_command(command)

    if success:
        print("✅ Admin канал создан!")
        return True
    else:
        print(f"❌ Ошибка создания admin канала: {stderr}")
        return False

def main():
    print("🚀 Создание каналов #vip и #admin в Rocket.Chat...")
    print("(Канал #general уже существует)")

    vip_ok = create_vip_channel()
    admin_ok = create_admin_channel()

    if vip_ok and admin_ok:
        print("\n✅ Все каналы успешно созданы!")
        print("🔄 Перезапускаю Rocket.Chat...")

        try:
            subprocess.run(['docker', 'restart', 'magic_beans_new-rocketchat-1'],
                          capture_output=True, text=True, timeout=60)
            print("✅ Rocket.Chat перезапущен!")

            print("\n🎉 КАНАЛЫ ГОТОВЫ К ИСПОЛЬЗОВАНИЮ!")
            print("📢 Доступные каналы:")
            print("1. #general - Общий чат (уже существовал)")
            print("2. #vip - VIP чат (создан)")
            print("3. #admin - Админский чат (создан)")

            print("\n🔗 Ссылки для тестирования:")
            print("📱 Rocket.Chat: http://127.0.0.1:3000")
            print("🧪 Тестовая страница: http://127.0.0.1:8001/chat/test/")

        except Exception as e:
            print(f"❌ Ошибка перезапуска: {e}")
    else:
        print("\n⚠️ Некоторые каналы не были созданы")

if __name__ == "__main__":
    main()
