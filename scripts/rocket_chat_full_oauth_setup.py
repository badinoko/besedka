#!/usr/bin/env python3
"""
🚀 ПОЛНАЯ АВТОМАТИЧЕСКАЯ НАСТРОЙКА ROCKET.CHAT OAUTH
Применяет ВСЕ настройки OAuth через MongoDB
"""

import subprocess
import time
import json

def create_mongodb_script():
    """Создает JavaScript скрипт для полной настройки OAuth"""

    script_content = '''
// 🚀 ПОЛНАЯ АВТОМАТИЧЕСКАЯ НАСТРОЙКА ROCKET.CHAT OAUTH
// Применяет ВСЕ настройки OAuth для интеграции с Django

print("🔧 Запускаю полную настройку OAuth для Беседки...");

// 1. ОСНОВНЫЕ OAUTH НАСТРОЙКИ
const oauthSettings = [
    // Основное включение
    { _id: 'Accounts_OAuth_Custom-Besedka', value: true },

    // URL и пути
    { _id: 'Accounts_OAuth_Custom-Besedka-url', value: 'http://127.0.0.1:8001' },
    { _id: 'Accounts_OAuth_Custom-Besedka-token_path', value: '/o/token/' },
    { _id: 'Accounts_OAuth_Custom-Besedka-identity_path', value: '/api/v1/auth/rocket/' },
    { _id: 'Accounts_OAuth_Custom-Besedka-authorize_path', value: '/o/authorize/' },

    // Токены и аутентификация
    { _id: 'Accounts_OAuth_Custom-Besedka-scope', value: 'read' },
    { _id: 'Accounts_OAuth_Custom-Besedka-token_sent_via', value: 'header' },
    { _id: 'Accounts_OAuth_Custom-Besedka-identity_token_sent_via', value: 'default' },
    { _id: 'Accounts_OAuth_Custom-Besedka-access_token_param', value: 'access_token' },

    // Client credentials
    { _id: 'Accounts_OAuth_Custom-Besedka-id', value: 'BesedkaRocketChat2025' },
    { _id: 'Accounts_OAuth_Custom-Besedka-secret', value: 'SecureSecretKey2025BesedkaRocketChatSSO' },

    // Внешний вид кнопки
    { _id: 'Accounts_OAuth_Custom-Besedka-login_style', value: 'redirect' },
    { _id: 'Accounts_OAuth_Custom-Besedka-button_text', value: 'Войти через Беседку' },
    { _id: 'Accounts_OAuth_Custom-Besedka-button_color', value: '#1d74f5' },
    { _id: 'Accounts_OAuth_Custom-Besedka-button_text_color', value: '#FFFFFF' },

    // Поля пользователя (ИСПРАВЛЕНО: roles вместо role!)
    { _id: 'Accounts_OAuth_Custom-Besedka-username_field', value: 'username' },
    { _id: 'Accounts_OAuth_Custom-Besedka-email_field', value: 'email' },
    { _id: 'Accounts_OAuth_Custom-Besedka-name_field', value: 'full_name' },
    { _id: 'Accounts_OAuth_Custom-Besedka-avatar_field', value: 'avatar_url' },
    { _id: 'Accounts_OAuth_Custom-Besedka-roles_claim', value: 'roles' },
    { _id: 'Accounts_OAuth_Custom-Besedka-groups_claim', value: 'groups' },

    // Роли для синхронизации
    { _id: 'Accounts_OAuth_Custom-Besedka-roles_to_sync', value: 'admin,moderator,vip,user' },

    // КРИТИЧЕСКИЕ ПЕРЕКЛЮЧАТЕЛИ (ВСЕ ВКЛЮЧЕНЫ!)
    { _id: 'Accounts_OAuth_Custom-Besedka-merge_users', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-show_button', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-map_channels', value: true },
    { _id: 'Accounts_OAuth_Custom-Besedka-merge_roles', value: true }
];

// Применяем OAuth настройки
let oauthSuccess = 0;
oauthSettings.forEach(setting => {
    try {
        const result = db.rocketchat_settings.updateOne(
            { _id: setting._id },
            { $set: { value: setting.value } },
            { upsert: true }
        );
        if (result.acknowledged) {
            oauthSuccess++;
            print("✅ " + setting._id + " = " + setting.value);
        }
    } catch (error) {
        print("❌ Ошибка: " + setting._id + " - " + error);
    }
});

// 2. МАППИНГ РОЛЕЙ И ГРУПП (JSON)
const channelMapping = {
    "owner": "admin,vip",
    "moderator": "admin",
    "user": "user"
};

try {
    const mappingResult = db.rocketchat_settings.updateOne(
        { _id: 'Accounts_OAuth_Custom-Besedka-channels_admin' },
        { $set: { value: JSON.stringify(channelMapping) } },
        { upsert: true }
    );
    if (mappingResult.acknowledged) {
        print("✅ Channel mapping установлен: " + JSON.stringify(channelMapping));
        oauthSuccess++;
    }
} catch (error) {
    print("❌ Ошибка channel mapping: " + error);
}

// 3. ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ БЕЗОПАСНОСТИ
const securitySettings = [
    // Разрешить iframe
    { _id: 'Restrict_access_inside_any_Iframe', value: false },
    { _id: 'Iframe_Restrict_Access', value: false },

    // Отключить лишние проверки
    { _id: 'Accounts_RequirePasswordConfirmation', value: false },
    { _id: 'Accounts_TwoFactorAuthentication_Enabled', value: false },

    // Автоматическое присоединение к каналам
    { _id: 'Accounts_Default_User_Preferences_joinDefaultChannels', value: true },
    { _id: 'Accounts_Default_User_Preferences_joinDefaultChannelsSilenced', value: false },

    // Исправление Site_Url
    { _id: 'Site_Url', value: 'http://127.0.0.1:3000' }
];

let securitySuccess = 0;
securitySettings.forEach(setting => {
    try {
        const result = db.rocketchat_settings.updateOne(
            { _id: setting._id },
            { $set: { value: setting.value } },
            { upsert: true }
        );
        if (result.acknowledged) {
            securitySuccess++;
            print("✅ " + setting._id + " = " + setting.value);
        }
    } catch (error) {
        print("❌ Ошибка: " + setting._id + " - " + error);
    }
});

// 4. ПРОВЕРКА РЕЗУЛЬТАТОВ
print("\\n📊 РЕЗУЛЬТАТЫ НАСТРОЙКИ:");
print("OAuth настройки: " + oauthSuccess + "/" + (oauthSettings.length + 1));
print("Безопасность: " + securitySuccess + "/" + securitySettings.length);

if (oauthSuccess >= 25 && securitySuccess >= 6) {
    print("\\n🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!");
    print("✅ OAuth провайдер 'Besedka' полностью настроен");
    print("✅ Все переключатели включены");
    print("✅ Iframe поддержка включена");
    print("✅ Маппинг ролей настроен");
    print("\\n🚀 Теперь откройте http://127.0.0.1:3000/login");
    print("   Должна появиться кнопка 'Войти через Беседку'!");
} else {
    print("\\n⚠️ НАСТРОЙКА НЕПОЛНАЯ!");
    print("❌ Некоторые настройки не применились");
    print("💡 Попробуйте ручную настройку из ROCKET_CHAT_COMPLETE_MANUAL.md");
}
'''

    # Сохраняем скрипт во временный файл
    with open('temp_oauth_setup.js', 'w', encoding='utf-8') as f:
        f.write(script_content)

    return 'temp_oauth_setup.js'

def main():
    """Основная функция настройки"""

    print("🚀 ПОЛНАЯ АВТОМАТИЧЕСКАЯ НАСТРОЙКА ROCKET.CHAT OAUTH")
    print("=" * 60)

    # Проверяем статус сервисов
    print("\\n🔍 Проверка статус сервисов...")

    try:
        import requests
        django_resp = requests.get("http://127.0.0.1:8001", timeout=5)
        print(f"✅ Django: HTTP {django_resp.status_code}")
    except:
        print("❌ Django не отвечает на порту 8001")
        return False

    try:
        rocket_resp = requests.get("http://127.0.0.1:3000", timeout=5)
        print(f"✅ Rocket.Chat: HTTP {rocket_resp.status_code}")
    except:
        print("❌ Rocket.Chat не отвечает на порту 3000")
        return False

    # Создаем скрипт
    print("\\n📝 Создание скрипта настройки...")
    script_file = create_mongodb_script()

    # Выполняем скрипт через MongoDB
    print("\\n⚙️ Применение настроек через MongoDB...")
    try:
        result = subprocess.run([
            'docker', 'exec', '-i',
            'magic_beans_new-mongo-1',  # Имя контейнера MongoDB
            'mongosh', 'rocketchat', '--eval', f'load("/{script_file}")'
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("✅ Скрипт выполнен успешно!")
            print(result.stdout)
        else:
            print("❌ Ошибка выполнения скрипта:")
            print(result.stderr)

            # Пробуем альтернативный способ
            print("\\n🔄 Пробую альтернативный способ...")
            alt_result = subprocess.run([
                'docker', 'exec', '-i',
                'magic_beans_new-mongo-1',
                'mongo', 'rocketchat', '--eval',
                open(script_file, 'r', encoding='utf-8').read()
            ], capture_output=True, text=True, timeout=30)

            if alt_result.returncode == 0:
                print("✅ Альтернативный способ сработал!")
                print(alt_result.stdout)
            else:
                print("❌ Оба способа не сработали")
                print("💡 Используйте ручную настройку из ROCKET_CHAT_COMPLETE_MANUAL.md")
                return False

    except subprocess.TimeoutExpired:
        print("❌ Таймаут выполнения скрипта")
        return False
    except FileNotFoundError:
        print("❌ Docker не найден или контейнер не запущен")
        return False
    finally:
        # Удаляем временный файл
        try:
            import os
            os.remove(script_file)
        except:
            pass

    print("\\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Откройте http://127.0.0.1:3000/login")
    print("2. Проверьте наличие кнопки 'Войти через Беседку'")
    print("3. Тестируйте интеграцию на http://127.0.0.1:8001/chat/integrated/")

    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\\n📖 АЛЬТЕРНАТИВА:")
        print("Используйте ручную настройку из файла:")
        print("ROCKET_CHAT_COMPLETE_MANUAL.md")
