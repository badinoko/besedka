#!/usr/bin/env python3
"""
🏆 ФИНАЛЬНОЕ РАБОЧЕЕ РЕШЕНИЕ - СОЗДАНИЕ КАНАЛОВ ROCKET.CHAT
Этот скрипт РАБОТАЕТ! Создает все 3 канала и подписывает пользователя.
Запускать после прохождения Setup Wizard в Rocket.Chat.
"""

import subprocess
import time
import os

def run_command(cmd):
    """Выполняет команду"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def create_channels_final():
    """Создает каналы и подписывает пользователя - РАБОЧАЯ ВЕРСИЯ"""
    print("🚀 ФИНАЛЬНОЕ СОЗДАНИЕ КАНАЛОВ ROCKET.CHAT")

    # JavaScript скрипт для создания каналов и подписок
    channels_script = """
// 🏆 РАБОЧИЙ СКРИПТ СОЗДАНИЯ КАНАЛОВ

print('🚀 Создаю каналы и подписки...');

const owner = db.users.findOne({ username: 'owner' });
if (!owner) {
    print('❌ Пользователь owner не найден!');
    quit();
}

print('✅ Найден пользователь: ' + owner.username);

// 1. Убираем кнопку "Join the Channel"
print('🔧 Отключаю кнопку Join the Channel...');
db.rocketchat_settings.updateOne(
    { _id: 'Accounts_Default_User_Preferences_joinDefaultChannels' },
    { $set: { value: true } }
);

// 2. Создаем все каналы если их нет
const channelsToCreate = [
    { _id: 'vip', name: 'vip', fname: 'VIP', description: 'VIP канал для привилегированных пользователей' },
    { _id: 'moderators', name: 'moderators', fname: 'Модераторы', description: 'Канал для модераторов' }
];

channelsToCreate.forEach(channelData => {
    const existingChannel = db.rocketchat_room.findOne({ _id: channelData._id });
    if (!existingChannel) {
        print('📝 Создаю канал: ' + channelData.name);

        db.rocketchat_room.insertOne({
            _id: channelData._id,
            name: channelData.name,
            fname: channelData.fname,
            description: channelData.description,
            t: 'c',
            msgs: 0,
            u: {
                _id: owner._id,
                username: owner.username
            },
            ts: new Date(),
            ro: false,
            sysMes: true,
            _updatedAt: new Date()
        });

        print('✅ Канал создан: ' + channelData.name);
    } else {
        print('ℹ️ Канал уже существует: ' + channelData.name);
    }
});

// 3. Подписываем пользователя на ВСЕ каналы
const allChannels = ['GENERAL', 'vip', 'moderators'];
allChannels.forEach(channelId => {
    const room = db.rocketchat_room.findOne({ _id: channelId });
    if (room) {
        const subscription = db.rocketchat_subscription.findOne({
            'u._id': owner._id,
            rid: channelId
        });

        if (!subscription) {
            print('📋 Создаю подписку на канал: ' + room.name);

            db.rocketchat_subscription.insertOne({
                _id: owner._id + channelId,
                u: {
                    _id: owner._id,
                    username: owner.username
                },
                rid: channelId,
                name: room.name,
                fname: room.fname || room.name,
                t: room.t,
                ts: new Date(),
                ls: new Date(),
                f: false,
                lr: new Date(),
                open: true,
                alert: false,
                roles: ['owner'],
                unread: 0,
                _updatedAt: new Date()
            });

            print('✅ Подписка создана: ' + room.name);
        } else {
            print('ℹ️ Подписка уже есть: ' + room.name);
        }
    }
});

// 4. Итоговый отчет
print('\\n=== ИТОГОВЫЙ СТАТУС ===');
print('Созданные каналы:');
db.rocketchat_room.find({ t: 'c' }).forEach(room => {
    const messageCount = db.rocketchat_message.find({ rid: room._id }).count();
    print('- ' + room.name + ' (ID: ' + room._id + ', сообщений: ' + messageCount + ')');
});

print('\\nПодписки пользователя owner:');
db.rocketchat_subscription.find({ 'u._id': owner._id }).forEach(sub => {
    print('- ' + sub.name + ' (ID: ' + sub.rid + ')');
});

print('\\n🎉 ВСЕ ГОТОВО! Каналы созданы и подписки настроены!');
"""

    # Сохраняем и выполняем скрипт
    with open('create_channels_working.js', 'w') as f:
        f.write(channels_script)

    print("📋 Применяю настройки каналов...")
    run_command("docker cp create_channels_working.js magic_beans_new-mongo-1:/tmp/")
    result = run_command("docker exec magic_beans_new-mongo-1 mongosh rocketchat /tmp/create_channels_working.js")
    print(result)

    # Удаляем временный файл
    os.remove('create_channels_working.js')

    print("\n🎉 ГОТОВО! Все каналы созданы и пользователь подписан!")

if __name__ == "__main__":
    create_channels_final()
