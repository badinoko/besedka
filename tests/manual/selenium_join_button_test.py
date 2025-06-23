#!/usr/bin/env python3
"""
🔍 SELENIUM ДИАГНОСТИКА: Поведение кнопки Join Channel
Создан по запросу пользователя для детального анализа проблемы
Дата: 23 июня 2025
"""

import os
import sys
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class JoinChannelDiagnostic:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8001"
        self.results = []

    def log(self, action, status, details=None):
        """Детальное логирование"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        entry = {
            'time': timestamp,
            'action': action,
            'status': status,
            'details': details or {}
        }
        self.results.append(entry)

        print(f"🕒 [{timestamp}] {action}: {status}")
        if details:
            for key, value in details.items():
                print(f"   └─ {key}: {value}")
        print()

    def setup_driver(self):
        """Настройка Chrome с логированием консоли"""
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")

        # Включаем все логи браузера
        chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

        self.log("Настройка", "Chrome драйвер запущен")

    def take_screenshot(self, name):
        """Скриншот с таймстампом"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/manual/screenshots/{timestamp}_{name}.png"

        # Создаем папку если нет
        os.makedirs("tests/manual/screenshots", exist_ok=True)

        self.driver.save_screenshot(filename)
        self.log("Скриншот", f"Сохранен: {name}", {"file": filename})
        return filename

    def get_browser_console_logs(self):
        """Получение логов консоли"""
        try:
            logs = self.driver.get_log('browser')
            errors = [log for log in logs if log['level'] in ['SEVERE', 'WARNING']]
            return errors
        except:
            return []

    def login_as_owner(self):
        """Авторизация под owner"""
        self.log("Авторизация", "Переход на страницу входа")

        self.driver.get(f"{self.base_url}/accounts/login/")
        self.take_screenshot("01_login_page")

        # Ввод данных
        username_field = self.wait.until(EC.presence_of_element_located((By.NAME, "login")))
        password_field = self.driver.find_element(By.NAME, "password")

        username_field.send_keys("owner")
        password_field.send_keys("owner123secure")

        self.take_screenshot("02_credentials_filled")

        # Вход
        submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        # Ожидание успешного входа
        self.wait.until(EC.url_contains("/news/"))
        self.log("Авторизация", "УСПЕШНО", {"url": self.driver.current_url})

    def navigate_to_chat(self):
        """Переход в интегрированный чат"""
        self.log("Навигация", "Переход в чат")

        self.driver.get(f"{self.base_url}/chat/integrated/")

        # Ждем загрузки iframe
        time.sleep(5)
        self.take_screenshot("03_chat_page_loaded")

        # Проверяем iframe
        try:
            iframe = self.wait.until(EC.presence_of_element_located((By.ID, "rocketChatFrame")))
            iframe_src = iframe.get_attribute("src")
            self.log("Iframe", "Найден", {"src": iframe_src})
        except:
            self.log("Iframe", "НЕ НАЙДЕН")

    def check_join_button_presence(self):
        """Детальная проверка кнопки Join"""
        try:
            iframe = self.driver.find_element(By.ID, "rocketChatFrame")
            self.driver.switch_to.frame(iframe)

            # Поиск элементов Join
            join_elements = []

            # Поиск по различным селекторам
            selectors = [
                "[data-qa='join-channel']",
                "button[aria-label*='Join']",
                ".join-channel",
                "button:contains('Join')",
                "*[contains(text(), 'Join')]",
                "*[contains(text(), 'Channel not joined')]"
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        join_elements.extend([{
                            'selector': selector,
                            'text': el.text,
                            'visible': el.is_displayed()
                        } for el in elements])
                except:
                    pass

            # Поиск по XPath для текста
            xpath_selectors = [
                "//*[contains(text(), 'Join')]",
                "//*[contains(text(), 'Channel not joined')]",
                "//button[contains(., 'Join')]"
            ]

            for xpath in xpath_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    if elements:
                        join_elements.extend([{
                            'xpath': xpath,
                            'text': el.text,
                            'visible': el.is_displayed(),
                            'tag': el.tag_name
                        } for el in elements])
                except:
                    pass

            self.driver.switch_to.default_content()

            if join_elements:
                self.log("Join Button", "🔴 НАЙДЕН", {"elements": join_elements})
                return True
            else:
                self.log("Join Button", "✅ НЕ НАЙДЕН")
                return False

        except Exception as e:
            self.driver.switch_to.default_content()
            self.log("Join Button", "ОШИБКА ПРОВЕРКИ", {"error": str(e)})
            return False

    def test_channel_switching(self):
        """Полный тест переключения каналов"""
        channels = ["Общий", "VIP", "Модераторы"]

        for i, channel_name in enumerate(channels):
            self.log("ТЕСТ КАНАЛА", f"=== {channel_name} ===")

            # Скриншот ДО
            self.take_screenshot(f"04_{i+1}_before_{channel_name}")

            # Логи консоли ДО
            console_before = self.get_browser_console_logs()

            try:
                # Поиск и клик по кнопке канала
                channel_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{channel_name}')]"))
                )

                self.log("Клик", f"Нажимаю кнопку {channel_name}")
                channel_button.click()

                # Ждем переключения и автозапуска auto_join_fix.js
                time.sleep(8)

                # Скриншот ПОСЛЕ клика
                self.take_screenshot(f"05_{i+1}_after_click_{channel_name}")

                # Проверяем iframe URL
                iframe = self.driver.find_element(By.ID, "rocketChatFrame")
                iframe_src = iframe.get_attribute("src")

                # Проверяем наличие Join Button
                has_join = self.check_join_button_presence()

                # Ждем завершения auto_join попыток (15 x 1.5 сек = 22.5 сек)
                self.log("Ожидание", "Auto join попытки (22 секунды)")
                time.sleep(22)

                # Финальный скриншот
                self.take_screenshot(f"06_{i+1}_final_{channel_name}")

                # Финальная проверка Join Button
                final_has_join = self.check_join_button_presence()

                # Логи консоли ПОСЛЕ
                console_after = self.get_browser_console_logs()
                new_errors = [log for log in console_after if log not in console_before]

                self.log("РЕЗУЛЬТАТ", f"Канал {channel_name}", {
                    "iframe_url": iframe_src,
                    "join_button_immediately": has_join,
                    "join_button_after_autojoin": final_has_join,
                    "new_console_errors": len(new_errors),
                    "error_messages": [log['message'][:100] for log in new_errors[:3]]
                })

            except Exception as e:
                self.log("ОШИБКА", f"Канал {channel_name}", {"exception": str(e)})
                self.take_screenshot(f"error_{i+1}_{channel_name}")

    def generate_report(self):
        """Генерация итогового отчета"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"tests/manual/join_button_diagnostic_report_{timestamp}.json"

        # Сохраняем детальные результаты
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        # Считаем статистику
        join_button_found = sum(1 for r in self.results
                               if r['action'] == 'Join Button' and '🔴 НАЙДЕН' in r['status'])

        total_channel_tests = sum(1 for r in self.results
                                 if r['action'] == 'ТЕСТ КАНАЛА')

        print("="*60)
        print("🎯 ИТОГОВЫЙ ОТЧЕТ ДИАГНОСТИКИ")
        print("="*60)
        print(f"📊 Всего действий: {len(self.results)}")
        print(f"🔴 Обнаружений Join Button: {join_button_found}")
        print(f"📁 Тестов каналов: {total_channel_tests}")
        print(f"📄 Подробный отчет: {report_file}")
        print(f"📸 Скриншоты: tests/manual/screenshots/")
        print("="*60)

        self.log("Отчет", "Сгенерирован", {"file": report_file})

    def run_full_diagnostic(self):
        """Запуск полной диагностики"""
        try:
            print("🚀 ЗАПУСК SELENIUM ДИАГНОСТИКИ JOIN CHANNEL")
            print("🎯 Цель: Детальный анализ поведения кнопки Join Channel")
            print("👤 Пользователь: owner")
            print("🔍 Каналы: Общий, VIP, Модераторы")
            print("-" * 60)

            self.setup_driver()
            self.login_as_owner()
            self.navigate_to_chat()
            self.test_channel_switching()
            self.generate_report()

            print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА УСПЕШНО!")
            return True

        except Exception as e:
            print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
            self.log("ФАТАЛЬНАЯ ОШИБКА", str(e))
            return False

        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()
                print("🔚 Chrome драйвер закрыт")

if __name__ == "__main__":
    diagnostic = JoinChannelDiagnostic()
    success = diagnostic.run_full_diagnostic()

    if not success:
        print("❌ Диагностика завершена с ошибками!")
        sys.exit(1)
