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

# Основная функция
def main():
    print("🚀 Попытка отключить требование подтверждения пароля")
    print("=" * 50)

    headers = login_to_rocketchat()
    if not headers:
        print("❌ Не удалось авторизоваться.")
        return

    print("\n🔧 Отключаем Accounts_RequirePasswordConfirmation...")

    # Пробуем отключить
    response = requests.post(
        f"{ROCKETCHAT_URL}/api/v1/settings/Accounts_RequirePasswordConfirmation",
        headers=headers,
        json={"value": False}
    )

    if response.status_code == 200:
        print("✅ Успешно отключено!")
        print("\n🎉 Теперь попробуйте запустить scripts/setup_rocketchat_oauth.py снова!")
    elif "TOTP Required" in response.text:
        print("❌ Заблокировано TOTP")
        print("\n💡 Попробуем альтернативный способ...")

        # Пробуем через метод админа
        admin_response = requests.post(
            f"{ROCKETCHAT_URL}/api/v1/method.call/saveSettings",
            headers=headers,
            json={
                "message": json.dumps({
                    "method": "saveSettings",
                    "params": [[{
                        "_id": "Accounts_RequirePasswordConfirmation",
                        "value": False
                    }]]
                })
            }
        )

        if admin_response.status_code == 200:
            print("✅ Альтернативный способ сработал!")
        else:
            print(f"❌ Альтернативный способ не сработал: {admin_response.text}")
    else:
        print(f"❌ Ошибка: {response.text}")

if __name__ == "__main__":
    main()
