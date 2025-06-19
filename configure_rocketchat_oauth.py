#!/usr/bin/env python3
"""
Скрипт для настройки Custom OAuth в Rocket.Chat через прямое подключение к MongoDB
"""
import subprocess
import json

# Настройки OAuth для Rocket.Chat
OAUTH_CONFIG = {
    'Accounts_OAuth_Custom_Besedka': True,
    'Accounts_OAuth_Custom_Besedka_url': 'http://127.0.0.1:8001',
    'Accounts_OAuth_Custom_Besedka_token_path': '/o/token/',
    'Accounts_OAuth_Custom_Besedka_identity_path': '/api/v1/auth/rocket/identity/',
    'Accounts_OAuth_Custom_Besedka_authorize_path': '/o/authorize/',
    'Accounts_OAuth_Custom_Besedka_scope': 'rocketchat',
    'Accounts_OAuth_Custom_Besedka_id': 'BesedkaRocketChat2025',
    'Accounts_OAuth_Custom_Besedka_secret': 'SecureSecretKey2025BesedkaRocketChatSSO',
    'Accounts_OAuth_Custom_Besedka_button_label_text': 'Sign in with Besedka',
    'Accounts_OAuth_Custom_Besedka_button_label_color': '#FFFFFF',
    'Accounts_OAuth_Custom_Besedka_button_color': '#007bff',
    'Accounts_OAuth_Custom_Besedka_login_style': 'redirect',
    'Accounts_OAuth_Custom_Besedka_key_field': 'username',
    'Accounts_OAuth_Custom_Besedka_username_field': 'username',
    'Accounts_OAuth_Custom_Besedka_email_field': 'email',
    'Accounts_OAuth_Custom_Besedka_name_field': 'name',
    'Accounts_OAuth_Custom_Besedka_roles_claim': 'role',
    'Accounts_OAuth_Custom_Besedka_merge_users': True,
    'Accounts_OAuth_Custom_Besedka_show_button': True,
}

def execute_mongo_command(command):
    """Выполняет команду в MongoDB через Docker"""
    cmd = [
        'docker', 'exec', '-i', 'magic_beans_new-mongo-1',
        'mongosh', 'rocketchat', '--eval', command
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def configure_oauth():
    """Настраивает Custom OAuth в Rocket.Chat"""
    print("🚀 Настройка Custom OAuth в Rocket.Chat...")

    success_count = 0
    total_count = len(OAUTH_CONFIG)

    for setting_key, setting_value in OAUTH_CONFIG.items():
        # Формируем команду для MongoDB
        if isinstance(setting_value, bool):
            value_str = 'true' if setting_value else 'false'
        else:
            value_str = f'"{setting_value}"'

        command = f'db.rocketchat_settings.updateOne({{_id: "{setting_key}"}}, {{$set: {{value: {value_str}}}}}, {{upsert: true}})'

        success, stdout, stderr = execute_mongo_command(command)

        if success:
            print(f"✅ {setting_key}")
            success_count += 1
        else:
            print(f"❌ {setting_key}: {stderr}")

    print(f"\n📊 Результат: {success_count}/{total_count} настроек применено")

    if success_count == total_count:
        print("✅ Все настройки OAuth успешно применены!")
        print("\n🔄 Теперь нужно перезапустить Rocket.Chat...")
        restart_rocketchat()
    else:
        print("⚠️ Некоторые настройки не были применены")

def restart_rocketchat():
    """Перезапускает Rocket.Chat контейнер"""
    print("🔄 Перезапуск Rocket.Chat...")

    try:
        # Останавливаем контейнер
        subprocess.run(['docker', 'restart', 'magic_beans_new-rocketchat-1'],
                      capture_output=True, text=True, timeout=60)
        print("✅ Rocket.Chat перезапущен!")

        # Ждем запуска
        import time
        print("⏳ Ожидание запуска...")
        time.sleep(10)

        print("🎯 Rocket.Chat готов к тестированию!")
        print_test_links()

    except Exception as e:
        print(f"❌ Ошибка перезапуска: {e}")

def print_test_links():
    """Выводит ссылки для тестирования"""
    print("\n🔗 ССЫЛКИ ДЛЯ ТЕСТИРОВАНИЯ:")
    print(f"📱 Rocket.Chat: http://127.0.0.1:3000")
    print(f"🧪 Тестовая страница: http://127.0.0.1:8001/chat/test/")
    print(f"🔐 Django OAuth: http://127.0.0.1:8001/o/authorize/?client_id=BesedkaRocketChat2025&redirect_uri=http://127.0.0.1:3000/_oauth/besedka&response_type=code&scope=rocketchat")

    print("\n📝 ИНСТРУКЦИЯ ТЕСТИРОВАНИЯ:")
    print("1. Откройте Rocket.Chat: http://127.0.0.1:3000")
    print("2. Нажмите кнопку 'Sign in with Besedka'")
    print("3. Если появится форма входа Django - войдите как owner/owner123secure")
    print("4. Вы должны автоматически войти в Rocket.Chat")

if __name__ == "__main__":
    configure_oauth()
