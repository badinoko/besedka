import requests
import json

# Параметры Rocket.Chat
ROCKETCHAT_URL = "http://127.0.0.1:3000"
ADMIN_USERNAME = "owner"
ADMIN_PASSWORD = input("Введите пароль админа Rocket.Chat: ")

# Функция для логина
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

# Функция для попытки отключить 2FA требования
def try_disable_2fa_requirements(headers):
    print("\n🔧 Попытка отключить 2FA требования через различные настройки...")

    # Список настроек, которые могут влиять на 2FA
    settings_to_try = [
        # Основные настройки 2FA
        ("Accounts_TwoFactorAuthentication_Enabled", False),
        ("Accounts_TwoFactorAuthentication_Enforce_Password_Fallback", False),
        ("Accounts_TwoFactorAuthentication_RememberFor", 1800),

        # API настройки
        ("API_Enable_CORS", True),
        ("API_CORS_Origin", "*"),

        # Безопасность
        ("Accounts_TwoFactorAuthentication_MaxDelta", 1),

        # Iframe настройки (заодно)
        ("Restrict_access_inside_any_Iframe", False),
        ("X_Frame_Options", ""),
    ]

    success_count = 0

    for setting_id, value in settings_to_try:
        print(f"\n📝 Пробуем настройку {setting_id}...")

        # Сначала проверяем текущее значение
        get_response = requests.get(
            f"{ROCKETCHAT_URL}/api/v1/settings/{setting_id}",
            headers=headers
        )

        if get_response.status_code == 200:
            current_value = get_response.json().get("value", "не найдено")
            print(f"   Текущее значение: {current_value}")

        # Пробуем изменить
        response = requests.post(
            f"{ROCKETCHAT_URL}/api/v1/settings/{setting_id}",
            headers=headers,
            json={"value": value}
        )

        if response.status_code == 200:
            print(f"   ✅ Успешно изменено на: {value}")
            success_count += 1
        elif "TOTP Required" in response.text:
            print(f"   ❌ Заблокировано TOTP")
        else:
            print(f"   ⚠️  Ошибка: {response.status_code}")

    print(f"\n📊 Итого успешно изменено настроек: {success_count}")

    # Попробуем еще один способ - через пользовательские настройки
    print("\n🔧 Пробуем отключить 2FA для текущего пользователя...")

    user_response = requests.post(
        f"{ROCKETCHAT_URL}/api/v1/users.2fa.disable",
        headers=headers,
        json={"userId": headers["X-User-Id"]}
    )

    if user_response.status_code == 200:
        print("✅ 2FA отключена для пользователя!")
    else:
        print(f"❌ Не удалось отключить 2FA: {user_response.text}")

# Основная функция
def main():
    print("🚀 Попытка отключить 2FA требования в Rocket.Chat")
    print("=" * 50)

    headers = login_to_rocketchat()
    if not headers:
        print("❌ Не удалось авторизоваться.")
        return

    try_disable_2fa_requirements(headers)

    print("\n" + "=" * 50)
    print("📌 Если ничего не помогло, придется отключить 2FA вручную:")
    print("1. Зайдите в Rocket.Chat")
    print("2. Аватар → My Account → Security → Two Factor Authentication")
    print("3. Отключите 2FA")
    print("4. Запустите scripts/setup_rocketchat_oauth.py")

if __name__ == "__main__":
    main()
