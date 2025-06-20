#!/usr/bin/env python3
# Скрипт для выполнения ВНУТРИ MongoDB Docker контейнера

from pymongo import MongoClient
from datetime import datetime
import sys

def fix_settings():
    client = MongoClient('mongodb://localhost:27017')
    db = client['rocketchat']
    settings = db['rocketchat_settings']

    updates = [
        ('Site_Url', 'http://127.0.0.1:3000'),
        ('Accounts_Default_User_Preferences_joinDefaultChannels', True),
        ('Accounts_Default_User_Preferences_joinDefaultChannelsSilenced', False),
        ('Accounts_Default_User_Preferences_openChannelsOnLogin', 'general'),
        ('Show_Setup_Wizard', False),
        ('First_Channel_After_Login', False),
        ('Accounts_TwoFactorAuthentication_Enabled', False),
        ('Accounts_RequirePasswordConfirmation', False),
        ('Restrict_access_inside_any_Iframe', False)
    ]

    for setting_id, value in updates:
        settings.update_one(
            {'_id': setting_id},
            {'$set': {'value': value, '_updatedAt': datetime.utcnow()}},
            upsert=True
        )
        print(f'✅ {setting_id}: {value}')

    print(f'🎉 Обновлено {len(updates)} настроек')
    client.close()

if __name__ == '__main__':
    fix_settings()
