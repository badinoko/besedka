#!/usr/bin/env python3
# ===================================================================
# СКРИПТ ИСПРАВЛЕНИЯ КРИТИЧЕСКИХ НАСТРОЕК ROCKET.CHAT
# Устраняет предупреждение URL и кнопку "Join the Channel"
# ===================================================================

import pymongo
import sys
from datetime import datetime

def fix_rocketchat_settings():
    """Исправление критических настроек Rocket.Chat через MongoDB"""

    try:
        # Подключение к MongoDB
        client = pymongo.MongoClient('mongodb://127.0.0.1:27017')
        print('🔗 Подключение к MongoDB успешно')

        db = client['rocketchat']
        settings_collection = db['rocketchat_settings']

        # ✅ 1. ИСПРАВЛЕНИЕ SITE URL - устраняет раздражающее предупреждение
        print('🔧 Исправляем Site URL...')
        settings_collection.update_one(
            {'_id': 'Site_Url'},
            {
                '$set': {
                    'value': 'http://127.0.0.1:3000',
                    'packageValue': 'http://127.0.0.1:3000',
                    'valueSource': 'packageValue',
                    'hidden': False,
                    'blocked': False,
                    'sorter': 1,
                    'i18nLabel': 'Site_Url',
                    'i18nDescription': 'Site_Url_Description',
                    'autocomplete': True,
                    'type': 'string',
                    'public': True,
                    'env': True,
                    'wizard': {
                        'step': 2,
                        'order': 0
                    },
                    '_updatedAt': datetime.utcnow()
                }
            },
            upsert=True
        )

        # ✅ 2. АВТОМАТИЧЕСКОЕ ПРИСОЕДИНЕНИЕ К КАНАЛАМ - убирает кнопку "Join the Channel"
        print('🔧 Настраиваем автоматическое присоединение...')

        # Accounts_Default_User_Preferences_joinDefaultChannels = true
        settings_collection.update_one(
            {'_id': 'Accounts_Default_User_Preferences_joinDefaultChannels'},
            {
                '$set': {
                    'value': True,
                    'packageValue': True,
                    'valueSource': 'packageValue',
                    'type': 'boolean',
                    'public': True,
                    'i18nLabel': 'Accounts_Default_User_Preferences_joinDefaultChannels',
                    '_updatedAt': datetime.utcnow()
                }
            },
            upsert=True
        )

        # Accounts_Default_User_Preferences_joinDefaultChannelsSilenced = false
        settings_collection.update_one(
            {'_id': 'Accounts_Default_User_Preferences_joinDefaultChannelsSilenced'},
            {
                '$set': {
                    'value': False,
                    'packageValue': False,
                    'valueSource': 'packageValue',
                    'type': 'boolean',
                    'public': True,
                    'i18nLabel': 'Accounts_Default_User_Preferences_joinDefaultChannelsSilenced',
                    '_updatedAt': datetime.utcnow()
                }
            },
            upsert=True
        )

        # ✅ 3. ОТКРЫТИЕ GENERAL КАНАЛА ПО УМОЛЧАНИЮ
        print('🔧 Настраиваем канал по умолчанию...')
        settings_collection.update_one(
            {'_id': 'Accounts_Default_User_Preferences_openChannelsOnLogin'},
            {
                '$set': {
                    'value': 'general',
                    'packageValue': 'general',
                    'valueSource': 'packageValue',
                    'type': 'string',
                    'public': True,
                    'i18nLabel': 'Accounts_Default_User_Preferences_openChannelsOnLogin',
                    '_updatedAt': datetime.utcnow()
                }
            },
            upsert=True
        )

        # ✅ 4. ОТКЛЮЧЕНИЕ ВСЕХ ЛИШНИХ ПРЕДУПРЕЖДЕНИЙ
        print('🔧 Отключаем лишние предупреждения...')

        warning_settings = [
            'Show_Setup_Wizard',
            'First_Channel_After_Login',
            'Accounts_TwoFactorAuthentication_Enabled',
            'Accounts_RequirePasswordConfirmation'
        ]

        for setting in warning_settings:
            settings_collection.update_one(
                {'_id': setting},
                {
                    '$set': {
                        'value': False,
                        'packageValue': False,
                        'valueSource': 'packageValue',
                        '_updatedAt': datetime.utcnow()
                    }
                },
                upsert=True
            )

        # ✅ 5. НАСТРОЙКИ IFRAME И БЕЗОПАСНОСТИ
        print('🔧 Настраиваем iframe и безопасность...')

        iframe_settings = [
            ('Restrict_access_inside_any_Iframe', False),
            ('Iframe_Restrict_Access', False),
            ('Iframe_X_Frame_Options', 'SAMEORIGIN')
        ]

        for setting_id, value in iframe_settings:
            settings_collection.update_one(
                {'_id': setting_id},
                {
                    '$set': {
                        'value': value,
                        'packageValue': value,
                        'valueSource': 'packageValue',
                        '_updatedAt': datetime.utcnow()
                    }
                },
                upsert=True
            )

        print('✅ Все настройки успешно применены!')
        print('📋 Применено исправлений:')
        print('   ✅ Site_Url: http://127.0.0.1:3000')
        print('   ✅ Автоматическое присоединение к каналам: включено')
        print('   ✅ Канал по умолчанию: general')
        print('   ✅ Предупреждения: отключены')
        print('   ✅ Iframe настройки: разрешены')

        # Показываем количество обновленных настроек
        total_settings = settings_collection.count_documents({})
        print(f'📊 Всего настроек в БД: {total_settings}')

    except pymongo.errors.ConnectionFailure:
        print('❌ Ошибка: Не удается подключиться к MongoDB на 127.0.0.1:27017')
        print('💡 Убедитесь, что MongoDB контейнер запущен:')
        print('   docker-compose -f docker-compose.local.yml up -d mongo')
        sys.exit(1)

    except Exception as error:
        print(f'❌ Ошибка при исправлении настроек: {error}')
        sys.exit(1)

    finally:
        client.close()
        print('🔒 Соединение с MongoDB закрыто')

if __name__ == '__main__':
    print('🚀 Запуск исправления настроек Rocket.Chat...')
    fix_rocketchat_settings()
    print('🎉 Исправления завершены! Перезапустите Rocket.Chat контейнер.')
