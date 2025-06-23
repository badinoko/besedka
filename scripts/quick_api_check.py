#!/usr/bin/env python3
"""
Быстрая проверка API Rocket.Chat для принудительной авторизации
"""

import requests
import json
from datetime import datetime

def quick_api_check():
    """Быстрая проверка возможностей API"""
    print("🚀 Быстрая проверка API Rocket.Chat")
    print("=" * 50)

    api_url = "http://127.0.0.1:3000/api/v1"

    # 1. Проверка доступности API
    print("1. Проверка API...")
    try:
        response = requests.get(f"{api_url}/info", timeout=5)
        if response.status_code == 200:
            info = response.json()
            print(f"✅ API доступен, версия: {info.get('version')}")
        else:
            print(f"❌ API недоступен: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return

    # 2. Авторизация администратора
    print("2. Авторизация администратора...")
    try:
        login_data = {"user": "owner", "password": "owner123secure"}
        auth_response = requests.post(f"{api_url}/login", json=login_data)

        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            user_id = auth_data["data"]["userId"]
            auth_token = auth_data["data"]["authToken"]
            print(f"✅ Авторизация успешна: {user_id}")

            headers = {
                "X-Auth-Token": auth_token,
                "X-User-Id": user_id,
                "Content-Type": "application/json"
            }

            # 3. Получение списка пользователей
            print("3. Получение пользователей...")
            users_response = requests.get(f"{api_url}/users.list", headers=headers)
            if users_response.status_code == 200:
                users_data = users_response.json()
                users = users_data.get("users", [])
                print(f"✅ Найдено пользователей: {len(users)}")
                for user in users:
                    print(f"   - {user['username']} (ID: {user['_id'][:8]}...)")

            # 4. Тест создания токена для другого пользователя
            print("4. Тест принудительной авторизации...")
            token_response = requests.post(
                f"{api_url}/users.createToken",
                json={"username": "test_user"},
                headers=headers
            )

            if token_response.status_code == 200:
                token_data = token_response.json()
                print(f"✅ Токен создан для test_user!")
                print(f"   Token: {token_data['data']['authToken'][:20]}...")

                # Тест токена
                test_headers = {
                    "X-Auth-Token": token_data["data"]["authToken"],
                    "X-User-Id": token_data["data"]["userId"],
                    "Content-Type": "application/json"
                }

                me_response = requests.get(f"{api_url}/me", headers=test_headers)
                if me_response.status_code == 200:
                    me_data = me_response.json()
                    print(f"✅ Принудительная авторизация РАБОТАЕТ: {me_data['username']}")
                    print("🎯 РЕШЕНИЕ: Можно использовать API для автоавторизации!")
                else:
                    print(f"❌ Токен не работает: {me_response.status_code}")
            else:
                print(f"❌ Не удалось создать токен: {token_response.status_code}")
                print(f"   Ответ: {token_response.text}")
        else:
            print(f"❌ Авторизация неудачна: {auth_response.status_code}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")

    print("=" * 50)
    print("📊 Анализ завершен")

if __name__ == "__main__":
    quick_api_check()
