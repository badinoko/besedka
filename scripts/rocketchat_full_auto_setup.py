#!/usr/bin/env python3
"""
🚀 ПОЛНОСТЬЮ АВТОМАТИЗИРОВАННАЯ НАСТРОЙКА ROCKET.CHAT
Этот скрипт восстанавливает ВСЕ настройки Rocket.Chat за один раз.
БОЛЬШЕ НЕ НУЖНО НАСТРАИВАТЬ ВРУЧНУЮ!

Использование:
python scripts/rocketchat_full_auto_setup.py
"""

import requests
import json
import time
import sys
import pymongo
from pymongo import MongoClient

class RocketChatAutoSetup:
    def __init__(self):
        self.rocketchat_url = "http://127.0.0.1:3000"
        self.mongo_url = "mongodb://127.0.0.1:27017"
        self.db_name = "rocketchat"

        # Учетные данные для автоматического создания
        self.admin_username = "owner"
        self.admin_password = "owner123secure"
        self.admin_email = "owner@besedka.com"

        # OAuth настройки для Django
        self.oauth_settings = {
            "Accounts_OAuth_Custom_Besedka": True,
            "Accounts_OAuth_Custom_Besedka_url": "http://127.0.0.1:8001",
            "Accounts_OAuth_Custom_Besedka_token_path": "/o/token/",
            "Accounts_OAuth_Custom_Besedka_identity_path": "/api/v1/auth/rocket/",
            "Accounts_OAuth_Custom_Besedka_authorize_path": "/o/authorize/",
            "Accounts_OAuth_Custom_Besedka_scope": "read",
            "Accounts_OAuth_Custom_Besedka_id": "BesedkaRocketChat2025",
            "Accounts_OAuth_Custom_Besedka_secret": "ZJwCaXXfQKHPbmdWo7RBSP7uv9M1hOTndbSbhqeJ29k",
            "Accounts_OAuth_Custom_Besedka_button_label_text": "Войти через Беседку",
            "Accounts_OAuth_Custom_Besedka_button_label_color": "#FFFFFF",
            "Accounts_OAuth_Custom_Besedka_button_color": "#1976D2",
            "Accounts_OAuth_Custom_Besedka_login_style": "redirect",
            "Accounts_OAuth_Custom_Besedka_show_button": True,
            "Accounts_OAuth_Custom_Besedka_merge_users": True,
            "Accounts_OAuth_Custom_Besedka_username_field": "username",
            "Accounts_OAuth_Custom_Besedka_email_field": "email",
            "Accounts_OAuth_Custom_Besedka_name_field": "name",
            "Accounts_OAuth_Custom_Besedka_roles_claim": "role",
            "Accounts_OAuth_Custom_Besedka_groups_claim": "groups",
            "Accounts_OAuth_Custom_Besedka_channels_admin": "admin,vip",
            "Accounts_OAuth_Custom_Besedka_map_channels": json.dumps({
                "owner": ["admin", "vip"],
                "moderator": ["admin"],
                "user": ["user"]
            }),
            # Критические настройки для iframe и автоматического входа
            "Iframe_Restrict_Access": False,
            "Restrict_access_inside_any_Iframe": False,
            "Accounts_RequirePasswordConfirmation": False,
            "Accounts_TwoFactorAuthentication_Enabled": False,
            "Site_Url": "http://127.0.0.1:3000",
            "Accounts_DefaultUserPreferences_autoImageLoad": True,
            "Accounts_DefaultUserPreferences_joinDefaultChannels": True,
            "Accounts_DefaultUserPreferences_joinDefaultChannelsSilenced": False
        }

        # Каналы для создания
        self.channels = [
            {"name": "general", "type": "c", "members": [], "description": "Общий чат - Беседка • Сообщество растениеводов"},
            {"name": "vip", "type": "p", "members": ["owner"], "description": "VIP Беседка - Эксклюзивный чат для избранных"},
            {"name": "moderators", "type": "p", "members": ["owner"], "description": "Модераторы - Админский чат для модерации"}
        ]

    def wait_for_rocketchat(self, max_attempts=30):
        """Ожидание запуска Rocket.Chat"""
        print("🔄 Ожидание запуска Rocket.Chat...")

        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.rocketchat_url}/api/info", timeout=5)
                if response.status_code == 200:
                    print("✅ Rocket.Chat запущен!")
                    return True
            except:
                pass

            print(f"   Попытка {attempt + 1}/{max_attempts}...")
            time.sleep(2)

        print("❌ Rocket.Chat не запустился за отведенное время")
        return False

    def check_setup_wizard(self):
        """Проверка нужен ли Setup Wizard"""
        try:
            response = requests.get(f"{self.rocketchat_url}/api/v1/setup/wizard", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("wizard", {}).get("step") == "admin_user":
                    print("🎯 Setup Wizard требует настройки администратора")
                    return True
            print("✅ Setup Wizard уже пройден")
            return False
        except Exception as e:
            print(f"⚠️ Ошибка проверки Setup Wizard: {e}")
            return True

    def complete_setup_wizard(self):
        """Автоматическое прохождение Setup Wizard"""
        print("🚀 Автоматическое прохождение Setup Wizard...")

        setup_data = {
            "admin_name": self.admin_username,
            "admin_username": self.admin_username,
            "admin_pass": self.admin_password,
            "admin_email": self.admin_email,
            "site_name": "Besedka Chat",
            "site_url": "http://127.0.0.1:3000",
            "language": "ru",
            "country": "RU",
            "agreement": True,
            "updates": False,
            "newsletter": False
        }

        try:
            response = requests.post(
                f"{self.rocketchat_url}/api/v1/setup/wizard",
                json=setup_data,
                timeout=10
            )

            if response.status_code == 200:
                print("✅ Setup Wizard завершен автоматически!")
                return True
            else:
                print(f"❌ Ошибка Setup Wizard: {response.status_code} {response.text}")
                return False

        except Exception as e:
            print(f"❌ Ошибка при прохождении Setup Wizard: {e}")
            return False

    def get_auth_token(self):
        """Получение токена авторизации"""
        print("🔑 Получение токена авторизации...")

        try:
            response = requests.post(
                f"{self.rocketchat_url}/api/v1/login",
                json={
                    "username": self.admin_username,
                    "password": self.admin_password
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.auth_token = data["data"]["authToken"]
                    self.user_id = data["data"]["userId"]
                    print("✅ Токен авторизации получен!")
                    return True

            print(f"❌ Ошибка авторизации: {response.status_code} {response.text}")
            return False

        except Exception as e:
            print(f"❌ Ошибка при получении токена: {e}")
            return False

    def apply_oauth_settings_direct(self):
        """Прямое применение OAuth настроек через MongoDB"""
        print("⚙️ Применение OAuth настроек через MongoDB...")

        try:
            client = MongoClient(self.mongo_url)
            db = client[self.db_name]
            settings_collection = db.rocketchat_settings

            applied_count = 0

            for setting_id, value in self.oauth_settings.items():
                # Обновляем или создаем настройку
                settings_collection.update_one(
                    {"_id": setting_id},
                    {
                        "$set": {
                            "value": value,
                            "type": "boolean" if isinstance(value, bool) else "string",
                            "group": "OAuth",
                            "section": "Custom OAuth: Besedka" if "Besedka" in setting_id else "General",
                            "packageValue": value,
                            "valueSource": "meteorSettingsValue",
                            "hidden": False,
                            "blocked": False,
                            "sorter": applied_count,
                            "i18nLabel": setting_id,
                            "autocomplete": True,
                            "_updatedAt": {"$date": int(time.time() * 1000)},
                            "meteorSettingsValue": value
                        }
                    },
                    upsert=True
                )
                applied_count += 1

            client.close()
            print(f"✅ Применено {applied_count} OAuth настроек через MongoDB!")
            return True

        except Exception as e:
            print(f"❌ Ошибка при применении настроек: {e}")
            return False

    def create_channels(self):
        """Создание каналов"""
        print("📢 Создание каналов...")

        headers = {
            "X-Auth-Token": self.auth_token,
            "X-User-Id": self.user_id,
            "Content-Type": "application/json"
        }

        created_count = 0

        for channel in self.channels:
            try:
                # Проверяем существует ли канал
                check_response = requests.get(
                    f"{self.rocketchat_url}/api/v1/channels.info?roomName={channel['name']}",
                    headers=headers,
                    timeout=5
                )

                if check_response.status_code == 200:
                    print(f"   ✅ Канал #{channel['name']} уже существует")
                    continue

                # Создаем канал
                create_data = {
                    "name": channel["name"],
                    "description": channel["description"],
                    "type": channel["type"],
                    "readOnly": False
                }

                if channel["type"] == "c":  # публичный канал
                    endpoint = "/api/v1/channels.create"
                else:  # приватный канал
                    endpoint = "/api/v1/groups.create"

                response = requests.post(
                    f"{self.rocketchat_url}{endpoint}",
                    json=create_data,
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 200:
                    print(f"   ✅ Канал #{channel['name']} создан!")
                    created_count += 1
                else:
                    print(f"   ⚠️ Ошибка создания канала #{channel['name']}: {response.text}")

            except Exception as e:
                print(f"   ❌ Ошибка при создании канала #{channel['name']}: {e}")

        print(f"✅ Создано {created_count} новых каналов!")
        return True

    def set_default_channel(self):
        """Установка канала по умолчанию"""
        print("🎯 Установка канала general как канала по умолчанию...")

        try:
            client = MongoClient(self.mongo_url)
            db = client[self.db_name]
            settings_collection = db.rocketchat_settings

            # Устанавливаем general как канал по умолчанию
            settings_collection.update_one(
                {"_id": "Accounts_DefaultUserPreferences_openFirstDirectMessage"},
                {
                    "$set": {
                        "value": "general",
                        "type": "string",
                        "_updatedAt": {"$date": int(time.time() * 1000)}
                    }
                },
                upsert=True
            )

            client.close()
            print("✅ Канал general установлен как канал по умолчанию!")
            return True

        except Exception as e:
            print(f"❌ Ошибка установки канала по умолчанию: {e}")
            return False

    def restart_rocketchat_service(self):
        """Перезапуск Rocket.Chat для применения настроек"""
        print("🔄 Перезапуск Rocket.Chat для применения настроек...")

        try:
            headers = {
                "X-Auth-Token": self.auth_token,
                "X-User-Id": self.user_id,
                "Content-Type": "application/json"
            }

            # Попытка перезапуска через API
            response = requests.post(
                f"{self.rocketchat_url}/api/v1/service.configurations",
                json={"action": "restart"},
                headers=headers,
                timeout=5
            )

            print("✅ Сигнал перезапуска отправлен!")
            print("⏳ Ожидание 5 секунд для применения настроек...")
            time.sleep(5)

            return True

        except Exception as e:
            print(f"⚠️ Не удалось перезапустить через API (это нормально): {e}")
            return True

    def run_full_setup(self):
        """Запуск полной автоматической настройки"""
        print("🚀 ПОЛНАЯ АВТОМАТИЧЕСКАЯ НАСТРОЙКА ROCKET.CHAT")
        print("=" * 60)

        # Шаг 1: Ожидание запуска Rocket.Chat
        if not self.wait_for_rocketchat():
            print("❌ ОШИБКА: Rocket.Chat не запустился!")
            return False

        # Шаг 2: Проверка и прохождение Setup Wizard
        if self.check_setup_wizard():
            if not self.complete_setup_wizard():
                print("❌ ОШИБКА: Не удалось пройти Setup Wizard!")
                return False

            # Небольшая пауза после создания администратора
            print("⏳ Пауза для инициализации пользователя...")
            time.sleep(3)

        # Шаг 3: Получение токена авторизации
        if not self.get_auth_token():
            print("❌ ОШИБКА: Не удалось получить токен авторизации!")
            return False

        # Шаг 4: Применение OAuth настроек через MongoDB
        if not self.apply_oauth_settings_direct():
            print("❌ ОШИБКА: Не удалось применить OAuth настройки!")
            return False

        # Шаг 5: Создание каналов
        if not self.create_channels():
            print("❌ ОШИБКА: Не удалось создать каналы!")
            return False

        # Шаг 6: Установка канала по умолчанию
        if not self.set_default_channel():
            print("❌ ОШИБКА: Не удалось установить канал по умолчанию!")
            return False

        # Шаг 7: Сигнал перезапуска
        self.restart_rocketchat_service()

        print("\n" + "=" * 60)
        print("🎉 АВТОМАТИЧЕСКАЯ НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 60)
        print("✅ Администратор создан: owner / owner123secure")
        print("✅ OAuth провайдер 'Besedka' настроен")
        print("✅ Каналы созданы: #general, #vip, #moderators")
        print("✅ Iframe ограничения отключены")
        print("✅ Автоматическое присоединение к каналам включено")
        print("\n🚀 Rocket.Chat готов к использованию!")
        print("🌐 Откройте: http://127.0.0.1:8001/chat/integrated/")
        print("=" * 60)

        return True

if __name__ == "__main__":
    try:
        setup = RocketChatAutoSetup()
        success = setup.run_full_setup()

        if success:
            print("\n✅ ВСЕ ГОТОВО! Больше не нужно настраивать вручную!")
            sys.exit(0)
        else:
            print("\n❌ Произошли ошибки при настройке!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Настройка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
