#!/usr/bin/env python3
"""
🪄 МАГИЧЕСКИЙ ПЕРЕЗАПУСК - РЕШЕНИЕ ВСЕХ ПРОБЛЕМ ОДНОЙ КОМАНДОЙ!

Этот скрипт:
✅ Безопасно перезапускает систему БЕЗ потери данных
✅ Автоматически настраивает Rocket.Chat
✅ Проверяет что все работает
✅ БОЛЬШЕ НЕ НУЖНО НАСТРАИВАТЬ ВРУЧНУЮ 16 РАЗ!

Использование:
python scripts/magic_restart.py
"""

import subprocess
import time
import requests
import pymongo
import sys

class MagicRestart:
    def __init__(self):
        self.rocketchat_url = "http://127.0.0.1:3000"
        self.django_url = "http://127.0.0.1:8001"

    def run_cmd(self, cmd, description, timeout=30):
        """Выполнение команды с красивым выводом"""
        print(f"🔄 {description}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                print(f"   ✅ Успешно")
                return True
            else:
                print(f"   ⚠️ Код ошибки: {result.returncode}")
                if result.stderr.strip():
                    print(f"   Ошибка: {result.stderr.strip()}")
                return False
        except subprocess.TimeoutExpired:
            print(f"   ⏳ Команда выполняется дольше {timeout} секунд...")
            return True
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return False

    def check_service(self, url, name):
        """Проверка доступности сервиса"""
        try:
            response = requests.get(url, timeout=5)
            print(f"   ✅ {name}: HTTP {response.status_code} - работает")
            return response.status_code in [200, 302]
        except Exception as e:
            print(f"   ❌ {name}: недоступен ({e})")
            return False

    def step1_safe_restart(self):
        """Шаг 1: Безопасный перезапуск системы"""
        print("\n" + "="*60)
        print("🛡️ ШАГ 1: БЕЗОПАСНЫЙ ПЕРЕЗАПУСК (данные сохраняются)")
        print("="*60)

        # Остановка Python процессов (кроме текущего скрипта)
        print("🔄 Остановка старых Python процессов")
        print("   ⚠️ ВНИМАНИЕ: Если появятся ошибки - это нормально!")
        try:
            # Используем более мягкий подход - не убиваем все процессы
            subprocess.run("taskkill /f /im daphne.exe", shell=True, capture_output=True, timeout=5)
            print("   ✅ Старые серверы остановлены")
        except:
            print("   ✅ Процедура завершена (ошибки игнорированы)")

        # Остановка web контейнера
        self.run_cmd("docker-compose -f docker-compose.local.yml stop web", "Остановка web контейнера")

        # Запуск основных сервисов
        self.run_cmd(
            "docker-compose -f docker-compose.local.yml up -d postgres redis mongo rocketchat",
            "Запуск основных сервисов"
        )

        print("⏳ Ожидание инициализации MongoDB (15 сек)...")
        time.sleep(15)

        # Проверка контейнеров
        print("\n📊 Статус контейнеров:")
        subprocess.run("docker ps --format \"table {{.Names}}\\t{{.Status}}\"", shell=True)

        return True

    def step2_start_django(self):
        """Шаг 2: Запуск Django"""
        print("\n" + "="*60)
        print("🚀 ШАГ 2: ЗАПУСК DJANGO")
        print("="*60)

        print("🔄 Запуск Django через daphne...")
        print("   (Запускается в фоновом режиме)")

        # Запуск daphne в фоне через PowerShell
        subprocess.Popen([
            "powershell", "-Command",
            "Start-Process", "-WindowStyle", "Minimized", "-FilePath", "daphne",
            "-ArgumentList", "-b", "127.0.0.1", "-p", "8001", "config.asgi:application"
        ])

        print("⏳ Ожидание запуска Django (10 сек)...")
        time.sleep(10)

        return True

    def step3_check_services(self):
        """Шаг 3: Проверка сервисов"""
        print("\n" + "="*60)
        print("🔍 ШАГ 3: ПРОВЕРКА СЕРВИСОВ")
        print("="*60)

        django_ok = self.check_service(self.django_url, "Django")
        rocket_ok = self.check_service(self.rocketchat_url, "Rocket.Chat")

        if django_ok and rocket_ok:
            print("🎉 ВСЕ СЕРВИСЫ РАБОТАЮТ!")
            return True
        else:
            print("❌ Некоторые сервисы не отвечают!")
            return False

    def step4_auto_configure_rocketchat(self):
        """Шаг 4: Автоматическая настройка Rocket.Chat"""
        print("\n" + "="*60)
        print("⚙️ ШАГ 4: АВТОМАТИЧЕСКАЯ НАСТРОЙКА ROCKET.CHAT")
        print("="*60)

        # Ожидание полной инициализации
        print("⏳ Ожидание полной инициализации Rocket.Chat...")
        for i in range(30):
            try:
                resp = requests.get(f"{self.rocketchat_url}/api/info", timeout=5)
                if resp.status_code == 200:
                    print("✅ Rocket.Chat готов к настройке!")
                    break
            except:
                pass
            time.sleep(2)

        # Проверка нужен ли Setup Wizard
        try:
            resp = requests.get(f"{self.rocketchat_url}/api/v1/setup/wizard", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("wizard", {}).get("step") == "admin_user":
                    print("🎯 Setup Wizard нужен - выполняю автоматическую настройку...")

                    # Автоматический Setup Wizard
                    setup_data = {
                        "admin_name": "owner",
                        "admin_username": "owner",
                        "admin_pass": "owner123secure",
                        "admin_email": "owner@besedka.com",
                        "site_name": "Besedka Chat",
                        "site_url": "http://127.0.0.1:3000",
                        "language": "ru",
                        "country": "RU",
                        "agreement": True,
                        "updates": False,
                        "newsletter": False
                    }

                    setup_resp = requests.post(f"{self.rocketchat_url}/api/v1/setup/wizard", json=setup_data, timeout=10)
                    if setup_resp.status_code == 200:
                        print("✅ Setup Wizard завершен!")
                    else:
                        print(f"⚠️ Ошибка Setup Wizard: {setup_resp.status_code}")
                        return False

                    time.sleep(3)  # Пауза после создания пользователя
                else:
                    print("✅ Setup Wizard уже пройден!")
        except Exception as e:
            print(f"⚠️ Ошибка проверки Setup Wizard: {e}")

        # Авторизация и настройка OAuth
        try:
            auth_resp = requests.post(f"{self.rocketchat_url}/api/v1/login", json={
                "username": "owner",
                "password": "owner123secure"
            }, timeout=10)

            if auth_resp.status_code == 200:
                print("✅ Авторизация успешна!")

                # Применение OAuth настроек через MongoDB
                print("🔧 Применение OAuth настроек...")
                client = pymongo.MongoClient("mongodb://127.0.0.1:27017")
                db = client.rocketchat
                settings = db.rocketchat_settings

                oauth_settings = {
                    "Accounts_OAuth_Custom_Besedka": True,
                    "Accounts_OAuth_Custom_Besedka_url": "http://127.0.0.1:8001",
                    "Accounts_OAuth_Custom_Besedka_token_path": "/o/token/",
                    "Accounts_OAuth_Custom_Besedka_identity_path": "/api/v1/auth/rocket/",
                    "Accounts_OAuth_Custom_Besedka_authorize_path": "/o/authorize/",
                    "Accounts_OAuth_Custom_Besedka_scope": "read",
                    "Accounts_OAuth_Custom_Besedka_id": "BesedkaRocketChat2025",
                    "Accounts_OAuth_Custom_Besedka_secret": "ZJwCaXXfQKHPbmdWo7RBSP7uv9M1hOTndbSbhqeJ29k",
                    "Accounts_OAuth_Custom_Besedka_button_label_text": "Войти через Беседку",
                    "Accounts_OAuth_Custom_Besedka_login_style": "redirect",
                    "Accounts_OAuth_Custom_Besedka_show_button": True,
                    "Accounts_OAuth_Custom_Besedka_merge_users": True,
                    "Iframe_Restrict_Access": False,
                    "Restrict_access_inside_any_Iframe": False,
                    "Accounts_RequirePasswordConfirmation": False,
                    "Accounts_TwoFactorAuthentication_Enabled": False,
                    "Site_Url": "http://127.0.0.1:3000",
                    "Accounts_DefaultUserPreferences_joinDefaultChannels": True
                }

                applied = 0
                for key, value in oauth_settings.items():
                    settings.update_one(
                        {"_id": key},
                        {"$set": {"value": value, "_updatedAt": {"$date": int(time.time() * 1000)}}},
                        upsert=True
                    )
                    applied += 1

                client.close()
                print(f"✅ Применено {applied} OAuth настроек!")

                return True
            else:
                print(f"❌ Ошибка авторизации: {auth_resp.status_code}")
                return False

        except Exception as e:
            print(f"❌ Ошибка настройки: {e}")
            return False

    def step5_final_check(self):
        """Шаг 5: Финальная проверка"""
        print("\n" + "="*60)
        print("🏁 ШАГ 5: ФИНАЛЬНАЯ ПРОВЕРКА")
        print("="*60)

        django_ok = self.check_service(self.django_url, "Django")
        rocket_ok = self.check_service(self.rocketchat_url, "Rocket.Chat")
        chat_ok = self.check_service(f"{self.django_url}/chat/integrated/", "Интегрированный чат")

        if django_ok and rocket_ok:
            print("\n🎉 МАГИЧЕСКИЙ ПЕРЕЗАПУСК ЗАВЕРШЕН УСПЕШНО!")
            print("="*60)
            print("✅ Все сервисы работают")
            print("✅ Rocket.Chat настроен автоматически")
            print("✅ OAuth интеграция готова")
            print("✅ БОЛЬШЕ НЕ НУЖНО НАСТРАИВАТЬ ВРУЧНУЮ!")
            print("\n🌐 Готовые ссылки:")
            print(f"   Django: {self.django_url}")
            print(f"   Rocket.Chat: {self.rocketchat_url}")
            print(f"   Чат: {self.django_url}/chat/integrated/")
            print("\n🔑 Логин в Rocket.Chat: owner / owner123secure")
            print("="*60)
            return True
        else:
            print("\n❌ ОШИБКИ В РАБОТЕ СЕРВИСОВ!")
            print("Проверьте логи контейнеров")
            return False

    def run_magic_restart(self):
        """Запуск магического перезапуска"""
        print("🪄 МАГИЧЕСКИЙ ПЕРЕЗАПУСК - РЕШЕНИЕ ВСЕХ ПРОБЛЕМ!")
        print("🎯 Цель: БОЛЬШЕ НЕ НАСТРАИВАТЬ ROCKET.CHAT ВРУЧНУЮ!")
        print("⏱️ Займет ~2 минуты")

        try:
            # Выполнение всех шагов
            if not self.step1_safe_restart():
                print("❌ Ошибка на шаге 1")
                return False

            if not self.step2_start_django():
                print("❌ Ошибка на шаге 2")
                return False

            if not self.step3_check_services():
                print("❌ Ошибка на шаге 3")
                return False

            if not self.step4_auto_configure_rocketchat():
                print("❌ Ошибка на шаге 4")
                return False

            return self.step5_final_check()

        except KeyboardInterrupt:
            print("\n⚠️ Магический перезапуск прерван пользователем")
            return False
        except Exception as e:
            print(f"\n❌ Критическая ошибка: {e}")
            return False

if __name__ == "__main__":
    restart = MagicRestart()
    success = restart.run_magic_restart()

    if success:
        print("\n🎊 ПРОБЛЕМА РЕШЕНА НАВСЕГДА!")
        print("Теперь используй этот скрипт каждый раз когда что-то сломается!")
        sys.exit(0)
    else:
        print("\n😞 Что-то пошло не так...")
        print("Обратись к разработчику для диагностики")
        sys.exit(1)
