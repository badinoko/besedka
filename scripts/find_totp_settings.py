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

# Функция для поиска настроек
def find_totp_settings(headers):
    print("\n🔍 Поиск всех настроек связанных с TOTP и 2FA...")

    # Получаем ВСЕ настройки
    response = requests.get(
        f"{ROCKETCHAT_URL}/api/v1/settings",
        headers=headers
    )

    if response.status_code == 200:
        settings = response.json().get("settings", [])
        print(f"📊 Всего настроек найдено: {len(settings)}")

        # Фильтруем настройки связанные с TOTP, 2FA, Auth
        relevant_keywords = ["totp", "2fa", "twofactor", "auth", "security", "admin"]
        relevant_settings = []

        for setting in settings:
            setting_id = setting.get("_id", "").lower()
            for keyword in relevant_keywords:
                if keyword in setting_id:
                    relevant_settings.append(setting)
                    break

        print(f"\n📋 Найдено релевантных настроек: {len(relevant_settings)}")

        # Выводим найденные настройки
        for setting in relevant_settings:
            print(f"\n🔹 {setting.get('_id')}")
            print(f"   Значение: {setting.get('value')}")
            print(f"   Тип: {setting.get('type')}")
            if setting.get('public'):
                print(f"   Публичная: Да")

        # Ищем конкретные настройки
        print("\n🎯 Проверяем критические настройки:")
        critical_settings = [
            "Accounts_TwoFactorAuthentication_Enforce_For_Admin_Route",
            "Accounts_TwoFactorAuthentication_Enforce_For_Admin",
            "API_Force_Auth_To_Settings_Modify",
            "Accounts_RequirePasswordConfirmation"
        ]

        for setting_id in critical_settings:
            response = requests.get(
                f"{ROCKETCHAT_URL}/api/v1/settings/{setting_id}",
                headers=headers
            )
            if response.status_code == 200:
                value = response.json().get("value", "не найдено")
                print(f"\n   {setting_id}: {value}")
            else:
                print(f"\n   {setting_id}: не найдено")

    else:
        print(f"❌ Не удалось получить настройки: {response.text}")

# Основная функция
def main():
    print("🚀 Поиск настроек TOTP в Rocket.Chat")
    print("=" * 50)

    headers = login_to_rocketchat()
    if not headers:
        print("❌ Не удалось авторизоваться.")
        return

    find_totp_settings(headers)

    print("\n" + "=" * 50)
    print("\n💡 ВАЖНО: Ищите настройки типа:")
    print("- Enforce_For_Admin")
    print("- RequirePasswordConfirmation")
    print("- Force_Auth_To_Settings_Modify")

if __name__ == "__main__":
    main()
