#!/usr/bin/env python3
"""
Автоматизированный тест интеграции Rocket.Chat с проектом Беседка
Диагностирует проблемы с подключением и OAuth
"""

import requests
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import sys

class RocketChatIntegrationTester:
    def __init__(self):
        self.django_url = "http://127.0.0.1:8001"
        self.rocketchat_url = "http://127.0.0.1:3000"
        self.test_page_url = f"{self.django_url}/chat/test/"

        # Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-web-security")
        self.chrome_options.add_argument("--allow-running-insecure-content")

        self.driver = None

    def setup_driver(self):
        """Инициализация WebDriver"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.set_window_size(1920, 1080)
            print("✅ WebDriver инициализирован")
            return True
        except Exception as e:
            print(f"❌ Ошибка инициализации WebDriver: {e}")
            return False

    def test_django_server(self):
        """Проверка работы Django сервера"""
        try:
            response = requests.get(self.django_url, timeout=10)
            if response.status_code == 200:
                print("✅ Django сервер работает")
                return True
            else:
                print(f"❌ Django сервер недоступен: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка подключения к Django: {e}")
            return False

    def test_rocketchat_server(self):
        """Проверка работы Rocket.Chat сервера"""
        try:
            response = requests.get(self.rocketchat_url, timeout=10)
            if response.status_code == 200:
                print("✅ Rocket.Chat сервер работает")
                return True
            else:
                print(f"❌ Rocket.Chat сервер недоступен: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка подключения к Rocket.Chat: {e}")
            return False

    def test_oauth_endpoints(self):
        """Проверка OAuth endpoints"""
        oauth_url = f"{self.django_url}/o/authorize/"
        try:
            params = {
                'client_id': 'BesedkaRocketChat2025',
                'redirect_uri': 'http://127.0.0.1:3000/_oauth/besedka',
                'response_type': 'code',
                'scope': 'rocketchat'
            }
            response = requests.get(oauth_url, params=params, timeout=10, allow_redirects=False)
            print(f"✅ OAuth endpoint доступен: {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ Ошибка OAuth endpoints: {e}")
            return False

    def test_chat_test_page(self):
        """Проверка тестовой страницы чата"""
        if not self.driver:
            print("❌ WebDriver не инициализирован")
            return False

        try:
            print("🔄 Загружаем тестовую страницу чата...")
            self.driver.get(self.test_page_url)

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            print("✅ Тестовая страница загружена")

            try:
                iframe = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "iframe"))
                )
                print("✅ Iframe найден")

                self.driver.switch_to.frame(iframe)
                time.sleep(5)

                page_source = self.driver.page_source

                if "We're not connected" in page_source or "Мы не подключены" in page_source:
                    print("❌ ПРОБЛЕМА НАЙДЕНА: 'Мы не подключены'")
                    return False
                elif "rocket.chat" in page_source.lower():
                    print("✅ Rocket.Chat контент загружен")
                    return True
                else:
                    print("❓ Неопределенное состояние Rocket.Chat")
                    print(f"Первые 500 символов: {page_source[:500]}")
                    return False

            except TimeoutException:
                print("❌ Iframe не найден или не загрузился")
                return False

        except Exception as e:
            print(f"❌ Ошибка при тестировании страницы: {e}")
            return False
        finally:
            self.driver.switch_to.default_content()

    def run_full_test(self):
        """Запуск полного теста"""
        print("🚀 ЗАПУСК ПОЛНОЙ ДИАГНОСТИКИ ROCKET.CHAT ИНТЕГРАЦИИ")
        print("=" * 60)

        tests = [
            ("Django сервер", self.test_django_server),
            ("Rocket.Chat сервер", self.test_rocketchat_server),
            ("OAuth endpoints", self.test_oauth_endpoints),
        ]

        for test_name, test_func in tests:
            print(f"\n🔍 Тест: {test_name}")
            result = test_func()
            if not result:
                print(f"⚠️ Тест '{test_name}' провален")

        print(f"\n🔍 Тест: Интеграция в браузере")
        if self.setup_driver():
            browser_result = self.test_chat_test_page()
            if not browser_result:
                print("⚠️ Тест браузера провален")

            input("\n👀 Браузер остается открытым для ручной проверки. Нажмите Enter чтобы закрыть...")
            self.driver.quit()

        print("\n" + "=" * 60)
        print("🏁 ДИАГНОСТИКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    tester = RocketChatIntegrationTester()
    tester.run_full_test()
