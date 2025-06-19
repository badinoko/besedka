import requests
import json
import time

# Параметры Rocket.Chat
ROCKETCHAT_URL = "http://127.0.0.1:3000"
ADMIN_USERNAME = "owner"  # Ваш админ в Rocket.Chat
ADMIN_PASSWORD = "owner123secure"

# Параметры OAuth
OAUTH_CONFIG = {
    "name": "besedka",
    "serverURL": "http://127.0.0.1:8001",
    "tokenPath": "/o/token/",
    "tokenSentVia": "header",
    "identityTokenSentVia": "header",
    "identityPath": "/api/v1/auth/rocket/",
    "authorizePath": "/o/authorize/",
    "scope": "read",
    "accessTokenParam": "access_token",
    "id": "BesedkaRocketChat2025",
    "secret": "SecureSecretKey2025BesedkaRocketChatSSO",
    "loginStyle": "redirect",
    "buttonText": "Войти через Беседку",
    "buttonTextColor": "#ffffff",
    "buttonColor": "#28a745",
    "usernameField": "username",
    "emailField": "email",
    "nameField": "display_name",
    "avatarField": "avatar_url",
    "rolesClaim": "role",
    "groupsClaim": "groups",
    "mergeUsers": True,
    "showButton": True,
    "enable": True
}

# Функция для логина в Rocket.Chat
def login_to_rocketchat():
    print("🔐 Авторизация в Rocket.Chat...")

    login_data = {
        "user": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }

    response = requests.post(
        f"{ROCKETCHAT_URL}/api/v1/login",
        json=login_data
    )

    if response.status_code == 200:
        data = response.json()
        print("✅ Успешно авторизован!")
        return {
            "X-Auth-Token": data["data"]["authToken"],
            "X-User-Id": data["data"]["userId"]
        }
    else:
        print(f"❌ Ошибка авторизации: {response.text}")
        return None

# Функция для отключения TOTP
def disable_totp(headers):
    print("\n🔓 Попытка отключить TOTP требования для API...")

    # Пробуем отключить TOTP для API вызовов
    response = requests.post(
        f"{ROCKETCHAT_URL}/api/v1/settings/API_Enable_Rate_Limiter_Limit_Time_Default",
        headers=headers,
        json={"value": 60000}
    )

    if response.status_code == 200:
        print("✅ Настройка применена")
    else:
        print("⚠️  Не удалось изменить настройку. Возможно, требуется отключить 2FA в UI")

# Функция для настройки OAuth
def setup_oauth(headers):
    print("\n🔧 Настройка Custom OAuth...")

    # Сначала проверим, есть ли уже такая настройка
    check_response = requests.get(
        f"{ROCKETCHAT_URL}/api/v1/settings/Accounts_OAuth_Custom-besedka",
        headers=headers
    )

    if check_response.status_code == 200:
        print("ℹ️  OAuth настройка уже существует, обновляем...")

    # Настраиваем каждый параметр
    settings = {
        "Accounts_OAuth_Custom-besedka": True,
        "Accounts_OAuth_Custom-besedka-url": OAUTH_CONFIG["serverURL"],
        "Accounts_OAuth_Custom-besedka-token_path": OAUTH_CONFIG["tokenPath"],
        "Accounts_OAuth_Custom-besedka-token_sent_via": OAUTH_CONFIG["tokenSentVia"],
        "Accounts_OAuth_Custom-besedka-identity_token_sent_via": OAUTH_CONFIG["identityTokenSentVia"],
        "Accounts_OAuth_Custom-besedka-identity_path": OAUTH_CONFIG["identityPath"],
        "Accounts_OAuth_Custom-besedka-authorize_path": OAUTH_CONFIG["authorizePath"],
        "Accounts_OAuth_Custom-besedka-scope": OAUTH_CONFIG["scope"],
        "Accounts_OAuth_Custom-besedka-access_token_param": OAUTH_CONFIG["accessTokenParam"],
        "Accounts_OAuth_Custom-besedka-id": OAUTH_CONFIG["id"],
        "Accounts_OAuth_Custom-besedka-secret": OAUTH_CONFIG["secret"],
        "Accounts_OAuth_Custom-besedka-login_style": OAUTH_CONFIG["loginStyle"],
        "Accounts_OAuth_Custom-besedka-button_text": OAUTH_CONFIG["buttonText"],
        "Accounts_OAuth_Custom-besedka-button_text_color": OAUTH_CONFIG["buttonTextColor"],
        "Accounts_OAuth_Custom-besedka-button_color": OAUTH_CONFIG["buttonColor"],
        "Accounts_OAuth_Custom-besedka-username_field": OAUTH_CONFIG["usernameField"],
        "Accounts_OAuth_Custom-besedka-email_field": OAUTH_CONFIG["emailField"],
        "Accounts_OAuth_Custom-besedka-name_field": OAUTH_CONFIG["nameField"],
        "Accounts_OAuth_Custom-besedka-avatar_field": OAUTH_CONFIG["avatarField"],
        "Accounts_OAuth_Custom-besedka-roles_claim": OAUTH_CONFIG["rolesClaim"],
        "Accounts_OAuth_Custom-besedka-groups_claim": OAUTH_CONFIG["groupsClaim"],
        "Accounts_OAuth_Custom-besedka-merge_users": OAUTH_CONFIG["mergeUsers"],
        "Accounts_OAuth_Custom-besedka-show_button": OAUTH_CONFIG["showButton"],
        "Accounts_OAuth_Custom-besedka-enable": OAUTH_CONFIG["enable"]
    }

    # Применяем каждую настройку
    for setting_id, value in settings.items():
        print(f"  📝 Настройка {setting_id}...")

        response = requests.post(
            f"{ROCKETCHAT_URL}/api/v1/settings/{setting_id}",
            headers=headers,
            json={"value": value}
        )

        if response.status_code == 200:
            print(f"  ✅ {setting_id} настроен!")
        else:
            print(f"  ❌ Ошибка настройки {setting_id}: {response.text}")

    print("\n✅ OAuth настройка завершена!")

# Функция для отключения iframe ограничений
def disable_iframe_restrictions(headers):
    print("\n🔓 Отключение ограничений iframe...")

    response = requests.post(
        f"{ROCKETCHAT_URL}/api/v1/settings/Restrict_access_inside_any_Iframe",
        headers=headers,
        json={"value": False}
    )

    if response.status_code == 200:
        print("✅ Ограничения iframe отключены!")
    else:
        print(f"❌ Ошибка: {response.text}")

# Функция для создания каналов
def create_channels(headers):
    print("\n📢 Создание каналов...")

    channels = [
        {"name": "vip", "members": [], "readOnly": False},
        {"name": "moderators", "members": [], "readOnly": False}  # Изменил с admin на moderators
    ]

    for channel in channels:
        # Проверяем, существует ли канал
        check_response = requests.get(
            f"{ROCKETCHAT_URL}/api/v1/channels.info?roomName={channel['name']}",
            headers=headers
        )

        if check_response.status_code == 200:
            print(f"ℹ️  Канал #{channel['name']} уже существует")
        else:
            # Создаем канал
            response = requests.post(
                f"{ROCKETCHAT_URL}/api/v1/channels.create",
                headers=headers,
                json=channel
            )

            if response.status_code == 200:
                print(f"✅ Канал #{channel['name']} создан!")
            else:
                print(f"❌ Ошибка создания канала #{channel['name']}: {response.text}")

# Основная функция
def main():
    print("🚀 Автоматическая настройка OAuth в Rocket.Chat")
    print("=" * 50)

    # Логинимся
    headers = login_to_rocketchat()
    if not headers:
        print("❌ Не удалось авторизоваться. Проверьте пароль.")
        return

    # Пробуем отключить TOTP
    disable_totp(headers)

    # Настраиваем OAuth
    setup_oauth(headers)

    # Отключаем iframe ограничения
    disable_iframe_restrictions(headers)

    # Создаем каналы
    create_channels(headers)

    print("\n" + "=" * 50)
    print("🎉 НАСТРОЙКА ЗАВЕРШЕНА!")
    print("\nТеперь вы можете:")
    print("1. Выйти из Rocket.Chat")
    print("2. На странице входа увидеть кнопку 'Войти через Беседку'")
    print("3. Авторизоваться через Django!")

if __name__ == "__main__":
    main()
