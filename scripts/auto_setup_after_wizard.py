#!/usr/bin/env python3
"""
Автоматическая настройка Rocket.Chat ПОСЛЕ прохождения Setup Wizard
Запускать сразу после создания пользователя через UI
"""

import subprocess
import time
import os

def run_command(cmd):
    """Выполняет команду"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def setup_rocketchat():
    """Настраивает Rocket.Chat после Setup Wizard"""
    print("Автоматическая настройка Rocket.Chat...")
    print("ВАЖНО: Запускайте этот скрипт ПОСЛЕ создания пользователя через Setup Wizard!")

    # Ждем 3 секунды
    print("\nЖду 3 секунды для завершения Setup Wizard...")
    time.sleep(3)

    # Создаем JS скрипт с полными настройками
    setup_script = """
// Полная автоматическая настройка Rocket.Chat для Беседки

print('Запускаю полную настройку Rocket.Chat...');

// 1. Исправляем раздражающее уведомление про порты
print('Исправляю настройки URL...');
db.rocketchat_settings.updateOne(
    { _id: 'Site_Url' },
    { $set: { value: 'http://127.0.0.1:3000' } }
);

// 2. Убираем кнопку "Join the Channel"
print('Отключаю кнопку Join the Channel...');
db.rocketchat_settings.updateOne(
    { _id: 'Accounts_Default_User_Preferences_joinDefaultChannels' },
    { $set: { value: true } }
);
db.rocketchat_settings.updateOne(
    { _id: 'Accounts_Default_User_Preferences_joinDefaultChannelsSilenced' },
    { $set: { value: false } }
);

// 3. Полные OAuth настройки для Беседки
print('Настраиваю OAuth для Беседки...');
const oauthSettings = [
    { _id: 'Accounts_OAuth_Custom-Besedka', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-url', value: 'http://127.0.0.1:8001' },
    { _id: 'Accounts_OAuth_Custom-Besedka-token_path', value: '/o/token/' },
    { _id: 'Accounts_OAuth_Custom-Besedka-identity_path', value: '/api/v1/auth/rocket/' },
    { _id: 'Accounts_OAuth_Custom-Besedka-authorize_path', value: '/o/authorize/' },
    { _id: 'Accounts_OAuth_Custom-Besedka-scope', value: 'read' },
    { _id: 'Accounts_OAuth_Custom-Besedka-token_sent_via', value: 'header' },
    { _id: 'Accounts_OAuth_Custom-Besedka-identity_token_sent_via', value: 'default' },
    { _id: 'Accounts_OAuth_Custom-Besedka-id', value: 'OhyXGbFxYqzOIFgSvdZqgfbFqoXqRHOqKdxArWwp' },
    { _id: 'Accounts_OAuth_Custom-Besedka-secret', value: 'z0nI7QezCmekBMtoKXDdxzxVz6FxNvQfkv4kESZGP1XWYXGHFvEcVbIZU1TorncflOQEBfpXgYLJh4yffVQ8ha7RVjo0VE4h6DPlYhMYrb85WRt3GMdp4LWSsR5jiV0y' },
    { _id: 'Accounts_OAuth_Custom-Besedka-login_style', value: 'redirect' },
    { _id: 'Accounts_OAuth_Custom-Besedka-button_label_text', value: 'Войти через Беседку' },
    { _id: 'Accounts_OAuth_Custom-Besedka-button_label_color', value: '#FFFFFF' },
    { _id: 'Accounts_OAuth_Custom-Besedka-button_color', value: '#1d74f5' },
    { _id: 'Accounts_OAuth_Custom-Besedka-username_field', value: 'username' },
    { _id: 'Accounts_OAuth_Custom-Besedka-email_field', value: 'email' },
    { _id: 'Accounts_OAuth_Custom-Besedka-name_field', value: 'full_name' },
    { _id: 'Accounts_OAuth_Custom-Besedka-avatar_field', value: 'avatar_url' },
    { _id: 'Accounts_OAuth_Custom-Besedka-roles_claim', value: 'roles' },
    { _id: 'Accounts_OAuth_Custom-Besedka-groups_claim', value: 'groups' },
    { _id: 'Accounts_OAuth_Custom-Besedka-channels_admin', value: 'admin,vip' },
    { _id: 'Accounts_OAuth_Custom-Besedka-merge_users', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-show_button', value: true }
];

// Применяем OAuth настройки
oauthSettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        { _id: setting._id },
        { $set: { value: setting.value } },
        { upsert: true }
    );
});

// 4. Основные настройки безопасности
print('Применяю настройки безопасности...');
const securitySettings = [
    { _id: 'Restrict_access_inside_any_Iframe', value: false },
    { _id: 'Accounts_RegistrationForm', value: 'Disabled' },
    { _id: 'Accounts_RequirePasswordConfirmation', value: false },
    { _id: 'Accounts_TwoFactorAuthentication_Enabled', value: false }
];

securitySettings.forEach(setting => {
    db.rocketchat_settings.updateOne(
        { _id: setting._id },
        { $set: { value: setting.value } },
        { upsert: true }
    );
});

// 5. Создаем все необходимые каналы
print('Создаю каналы...');
const owner = db.users.findOne({ username: 'owner' });

if (owner) {
    const channels = [
        { name: 'vip-chat', displayName: 'VIP чат', description: 'Приватный VIP чат для избранных участников' },
        { name: 'moderators', displayName: 'Модераторы', description: 'Канал для модераторов и администрации' }
    ];

    channels.forEach(channel => {
        const existingChannel = db.rocketchat_room.findOne({ name: channel.name });
        if (!existingChannel) {
            db.rocketchat_room.insertOne({
                _id: channel.name,
                name: channel.name,
                fname: channel.displayName,
                description: channel.description,
                t: 'c',
                msgs: 0,
                u: {
                    _id: owner._id,
                    username: 'owner'
                },
                ts: new Date(),
                ro: false,
                sysMes: true,
                _updatedAt: new Date()
            });
            print('Создан канал: ' + channel.displayName);
        } else {
            print('Канал уже существует: ' + channel.displayName);
        }
    });
}

print('\\nНАСТРОЙКА ЗАВЕРШЕНА!');
print('OAuth настроен с полными параметрами');
print('Убрано раздражающее уведомление про порты');
print('Отключена кнопка Join the Channel');
print('Iframe ограничения отключены');
print('Регистрация отключена');
print('Созданы все каналы для тестирования');
"""

    # Сохраняем и выполняем скрипт
    with open('auto_complete_setup.js', 'w') as f:
        f.write(setup_script)

    print("\nПрименяю полные настройки Rocket.Chat...")
    run_command("docker cp auto_complete_setup.js magic_beans_new-mongo-1:/tmp/")
    result = run_command("docker exec magic_beans_new-mongo-1 mongosh rocketchat /tmp/auto_complete_setup.js")
    print(result)

    # Удаляем временный файл
    os.remove('auto_complete_setup.js')

    # Перезапускаем Rocket.Chat
    print("\nПерезапускаю Rocket.Chat...")
    run_command("docker restart magic_beans_new-rocketchat-1")

    # Создаем резервную копию
    print("\nСоздаю резервную копию...")
    run_command("python scripts/backup_rocketchat.py backup")

    print("\nГОТОВО! Теперь Rocket.Chat настроен и резервная копия создана!")
    print("В следующий раз просто запустите: python scripts/backup_rocketchat.py restore")

if __name__ == "__main__":
    setup_rocketchat()
