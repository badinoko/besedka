#!/usr/bin/env python3
"""
Скрипт для включения iframe поддержки в Rocket.Chat
Исправляет критическую проблему с отключенными iframe настройками
"""

import pymongo
import sys
from datetime import datetime

def fix_iframe_settings():
    """Включает iframe поддержку в Rocket.Chat"""

    try:
        # Подключение к MongoDB
        client = pymongo.MongoClient('mongodb://localhost:27017/')
        db = client.rocketchat
        settings_collection = db.rocketchat_settings

        print("🔧 Исправляю iframe настройки...")

        # Настройки для включения iframe поддержки
        iframe_settings = [
            {
                '_id': 'Iframe_Integration_send_enable',
                'value': True,
                'valueSource': 'customValue'
            },
            {
                '_id': 'Iframe_Integration_receive_enable',
                'value': True,
                'valueSource': 'customValue'
            },
            {
                '_id': 'Iframe_Integration_send_target_origin',
                'value': '*',
                'valueSource': 'customValue'
            },
            {
                '_id': 'Iframe_Integration_receive_origin',
                'value': '*',
                'valueSource': 'customValue'
            }
        ]

        # Применяем настройки
        for setting in iframe_settings:
            result = settings_collection.update_one(
                {'_id': setting['_id']},
                {
                    '$set': {
                        'value': setting['value'],
                        'valueSource': setting['valueSource'],
                        '_updatedAt': datetime.utcnow()
                    }
                }
            )

            if result.modified_count > 0:
                print(f"✅ Включена настройка: {setting['_id']} = {setting['value']}")
            else:
                print(f"⚠️  Настройка {setting['_id']} уже включена")

        print("\n🎉 IFRAME ПОДДЕРЖКА ВКЛЮЧЕНА!")
        print("🔄 Перезапустите Rocket.Chat для применения изменений:")
        print("   docker restart magic_beans_new-rocketchat-1")

        return True

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    if fix_iframe_settings():
        sys.exit(0)
    else:
        sys.exit(1)
