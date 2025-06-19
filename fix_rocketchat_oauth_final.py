#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ СКРИПТ ИСПРАВЛЕНИЯ OAUTH ДЛЯ ROCKET.CHAT
Решает проблему popup блокировки и удаляет дублирующие OAuth провайдеры
"""
import subprocess
import json
import time
import os

def execute_mongo_command(command):
    """Выполняет команду в MongoDB через Docker с правильным экранированием"""
    # Экранируем команду для PowerShell
    escaped_command = command.replace('"', '\\"').replace('$', '\\$')

    cmd = [
        'docker', 'exec', '-i', 'magic_beans_new-mongo-1',
        'mongosh', 'rocketchat', '--eval', escaped_command
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=False)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def delete_duplicate_oauth_providers():
    """Удаляет дублирующие OAuth провайдеры"""
    print("\n🧹 УДАЛЕНИЕ ДУБЛИРУЮЩИХ OAUTH ПРОВАЙДЕРОВ...")

    duplicates = [
        'Accounts_OAuth_Custom_besedka',
        'Accounts_OAuth_Custom_besedka_merge_users',
        'Accounts_OAuth_Custom_besedka_show_button',
        'Accounts_OAuth_Custom_workingbesedka'
    ]

    for duplicate in duplicates:
        # Находим все настройки с этим префиксом
        command = f'db.rocketchat_settings.deleteMany({{_id: {{\\$regex: "^{duplicate}"}}}});'
        success, stdout, stderr = execute_mongo_command(command)

        if success:
            print(f"✅ Удален: {duplicate}")
        else:
            print(f"⚠️ Не удалось удалить {duplicate}: {stderr}")

def fix_oauth_login_style():
    """Исправляет login_style с popup на redirect"""
    print("\n🔧 ИСПРАВЛЕНИЕ LOGIN_STYLE НА REDIRECT...")

    # Основные настройки OAuth
    settings = {
        'Accounts_OAuth_Custom_Besedka': True,
        'Accounts_OAuth_Custom_Besedka_login_style': 'redirect',  # КРИТИЧЕСКИ ВАЖНО!
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
        'Accounts_OAuth_Custom_Besedka_key_field': 'username',
        'Accounts_OAuth_Custom_Besedka_username_field': 'username',
        'Accounts_OAuth_Custom_Besedka_email_field': 'email',
        'Accounts_OAuth_Custom_Besedka_name_field': 'name',
        'Accounts_OAuth_Custom_Besedka_roles_claim': 'role',
        'Accounts_OAuth_Custom_Besedka_merge_users': True,
        'Accounts_OAuth_Custom_Besedka_show_button': True,
    }

    success_count = 0
    total_count = len(settings)

    for setting_key, setting_value in settings.items():
        # Формируем значение для MongoDB
        if isinstance(setting_value, bool):
            value_str = 'true' if setting_value else 'false'
        else:
            value_str = f'\\"{setting_value}\\"'

        # Используем updateOne с upsert
        command = f'db.rocketchat_settings.updateOne({{_id: \\"{setting_key}\\"}}, {{\\$set: {{value: {value_str}}}}}, {{upsert: true}});'

        success, stdout, stderr = execute_mongo_command(command)

        if success:
            print(f"✅ {setting_key}: {setting_value}")
            success_count += 1
        else:
            print(f"❌ {setting_key}: {stderr}")

    return success_count == total_count

def verify_settings():
    """Проверяет что настройки применены правильно"""
    print("\n🔍 ПРОВЕРКА ПРИМЕНЕНИЯ НАСТРОЕК...")

    # Проверяем критически важный параметр login_style
    command = 'db.rocketchat_settings.findOne({_id: \\"Accounts_OAuth_Custom_Besedka_login_style\\"});'
    success, stdout, stderr = execute_mongo_command(command)

    if success and 'redirect' in stdout:
        print("✅ login_style = redirect - УСПЕХ!")
        return True
    else:
        print("❌ login_style НЕ изменен на redirect!")
        return False

def restart_rocketchat():
    """Перезапускает Rocket.Chat для применения настроек"""
    print("\n🔄 ПЕРЕЗАПУСК ROCKET.CHAT...")

    try:
        subprocess.run(['docker', 'restart', 'magic_beans_new-rocketchat-1'],
                      capture_output=True, text=True, timeout=60)
        print("✅ Rocket.Chat перезапущен!")
        print("⏳ Ожидание запуска (15 секунд)...")
        time.sleep(15)
        return True
    except Exception as e:
        print(f"❌ Ошибка перезапуска: {e}")
        return False

def main():
    print("🚀 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ OAUTH ДЛЯ ROCKET.CHAT")
    print("=" * 60)

    # 1. Удаляем дубликаты
    delete_duplicate_oauth_providers()

    # 2. Исправляем login_style
    if fix_oauth_login_style():
        print("\n✅ ВСЕ НАСТРОЙКИ ПРИМЕНЕНЫ!")

        # 3. Проверяем результат
        if verify_settings():
            # 4. Перезапускаем Rocket.Chat
            if restart_rocketchat():
                print("\n🎉 УСПЕХ! OAUTH ИСПРАВЛЕН!")
                print("\n📋 ИНСТРУКЦИЯ ДЛЯ ПРОВЕРКИ:")
                print("1. Откройте http://127.0.0.1:3000")
                print("2. Нажмите кнопку 'Sign in with Besedka'")
                print("3. Вы должны быть ПЕРЕНАПРАВЛЕНЫ на страницу Django (НЕ popup!)")
                print("4. После входа в Django вы вернетесь в Rocket.Chat авторизованным")

                print("\n🔗 ТЕСТОВЫЕ ССЫЛКИ:")
                print(f"• Rocket.Chat: http://127.0.0.1:3000")
                print(f"• Django: http://127.0.0.1:8001")
                print(f"• Тестовая страница: http://127.0.0.1:8001/chat/test/")
            else:
                print("\n⚠️ Не удалось перезапустить Rocket.Chat")
        else:
            print("\n❌ Настройки не применились корректно")
    else:
        print("\n❌ Не удалось применить все настройки")

if __name__ == "__main__":
    main()
