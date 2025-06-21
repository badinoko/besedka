import requests
import json
import time
import pymongo

def setup_rocketchat():
    print("🚀 Автоматическая настройка Rocket.Chat")

    # Ожидание запуска
    print("Ожидание Rocket.Chat...")
    for i in range(30):
        try:
            resp = requests.get("http://127.0.0.1:3000/api/info", timeout=5)
            if resp.status_code == 200:
                break
        except:
            pass
        time.sleep(2)

    # Setup Wizard
    setup_data = {
        "admin_username": "owner",
        "admin_pass": "owner123secure",
        "admin_email": "owner@besedka.com",
        "site_name": "Besedka Chat"
    }

    try:
        resp = requests.post("http://127.0.0.1:3000/api/v1/setup/wizard", json=setup_data)
        print("Setup Wizard завершен")
    except:
        pass

    # Авторизация
    auth_resp = requests.post("http://127.0.0.1:3000/api/v1/login", json={
        "username": "owner",
        "password": "owner123secure"
    })

    if auth_resp.status_code == 200:
        print("✅ Авторизация успешна!")

        # MongoDB настройки
        client = pymongo.MongoClient("mongodb://127.0.0.1:27017")
        db = client.rocketchat
        settings = db.rocketchat_settings

        oauth_settings = {
            "Accounts_OAuth_Custom_Besedka": True,
            "Accounts_OAuth_Custom_Besedka_url": "http://127.0.0.1:8001",
            "Accounts_OAuth_Custom_Besedka_id": "BesedkaRocketChat2025",
            "Accounts_OAuth_Custom_Besedka_secret": "ZJwCaXXfQKHPbmdWo7RBSP7uv9M1hOTndbSbhqeJ29k",
            "Iframe_Restrict_Access": False,
            "Restrict_access_inside_any_Iframe": False
        }

        for key, value in oauth_settings.items():
            settings.update_one(
                {"_id": key},
                {"$set": {"value": value}},
                upsert=True
            )

        print("✅ OAuth настройки применены!")
        client.close()

    print("🎉 Настройка завершена!")

if __name__ == "__main__":
    setup_rocketchat()
