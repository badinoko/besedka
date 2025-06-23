#!/usr/bin/env python3
"""
Детальный анализ поведения кнопки "Join the Channel" в Rocket.Chat
Дата: 23 июня 2025 г.
Цель: Понять логику появления/исчезновения кнопки через визуальное тестирование
"""

import time
import json
import logging
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os

# Настройка логирования
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = Path("tests/logs")
log_dir.mkdir(exist_ok=True)

# Настройка детального логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'tests/logs/join_button_analysis_{timestamp}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JoinButtonAnalyzer:
    def __init__(self):
        self.timestamp = timestamp
        self.screenshots_dir = Path(f"tests/logs/screenshots_{timestamp}")
        self.screenshots_dir.mkdir(exist_ok=True)
        self.driver = None
        self.analysis_data = {
            "start_time": datetime.now().isoformat(),
            "screenshots": [],
            "join_button_states": [],
            "console_logs": [],
            "network_logs": [],
            "errors": []
        }
        self.screenshot_counter = 0

    def setup_driver(self):
        """Настройка Chrome драйвера с детальным логированием"""
        logger.info("🚀 Настройка Chrome драйвера...")

        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        # НЕ используем headless - нужна визуализация
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Включаем логирование (исправлен для новых версий Chrome)
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")
        chrome_options.set_capability("goog:loggingPrefs", {
            "browser": "ALL",
            "driver": "ALL",
            "performance": "ALL"
        })

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("✅ Chrome драйвер успешно настроен")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка настройки драйвера: {e}")
            return False

    def take_screenshot(self, description=""):
        """Создание скриншота с описанием"""
        self.screenshot_counter += 1
        filename = f"screenshot_{self.screenshot_counter:03d}_{description.replace(' ', '_')}.png"
        filepath = self.screenshots_dir / filename

        try:
            self.driver.save_screenshot(str(filepath))
            logger.info(f"📸 Скриншот сохранен: {filename}")

            self.analysis_data["screenshots"].append({
                "timestamp": datetime.now().isoformat(),
                "filename": filename,
                "description": description,
                "url": self.driver.current_url
            })
            return str(filepath)
        except Exception as e:
            logger.error(f"❌ Ошибка создания скриншота: {e}")
            return None

    def collect_console_logs(self):
        """Сбор логов консоли браузера"""
        try:
            logs = self.driver.get_log("browser")
            for log in logs:
                self.analysis_data["console_logs"].append({
                    "timestamp": datetime.now().isoformat(),
                    "level": log["level"],
                    "message": log["message"],
                    "source": log.get("source", "unknown")
                })
                logger.info(f"🔍 Console [{log['level']}]: {log['message']}")
        except Exception as e:
            logger.error(f"❌ Ошибка сбора логов консоли: {e}")

    def check_join_button_state(self, context=""):
        """Детальная проверка состояния кнопки Join Channel"""
        logger.info(f"🔍 Проверка кнопки Join Channel - {context}")

        state = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "url": self.driver.current_url,
            "join_button_present": False,
            "join_button_visible": False,
            "join_button_text": "",
            "iframe_loaded": False,
            "channel_name": "unknown",
            "user_subscribed": False
        }

        try:
            # Проверяем загрузку iframe
            iframe = self.driver.find_element(By.ID, "rocketChatFrame")
            if iframe:
                state["iframe_loaded"] = True
                iframe_src = iframe.get_attribute("src")
                logger.info(f"📡 Iframe URL: {iframe_src}")

                # Извлекаем имя канала из URL
                if "/channel/" in iframe_src:
                    channel_part = iframe_src.split("/channel/")[1].split("?")[0]
                    state["channel_name"] = channel_part

                # Переключаемся в iframe для поиска кнопки Join
                self.driver.switch_to.frame(iframe)

                # Ждем загрузки содержимого iframe
                time.sleep(3)

                # Поиск кнопки Join Channel разными способами
                join_button_selectors = [
                    "button:contains('Join')",
                    "[data-qa='join-room']",
                    ".rcx-button--primary:contains('Join')",
                    "button[title*='Join']",
                    "*[class*='join']:contains('Join')",
                    "button"  # Все кнопки для анализа
                ]

                for selector in join_button_selectors:
                    try:
                        if ":contains" in selector:
                            # Используем JavaScript для поиска по тексту
                            buttons = self.driver.execute_script("""
                                return Array.from(document.querySelectorAll('button')).filter(btn =>
                                    btn.textContent.toLowerCase().includes('join')
                                );
                            """)
                            if buttons:
                                state["join_button_present"] = True
                                state["join_button_visible"] = True
                                state["join_button_text"] = buttons[0].text if buttons else ""
                                logger.info(f"🎯 НАЙДЕНА кнопка Join: '{state['join_button_text']}'")
                                break
                        else:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                for elem in elements:
                                    text = elem.text.lower()
                                    if "join" in text:
                                        state["join_button_present"] = True
                                        state["join_button_visible"] = elem.is_displayed()
                                        state["join_button_text"] = elem.text
                                        logger.info(f"🎯 НАЙДЕНА кнопка Join: '{elem.text}'")
                                        break
                    except Exception as e:
                        continue

                # Собираем все кнопки для анализа
                all_buttons = self.driver.execute_script("""
                    return Array.from(document.querySelectorAll('button')).map(btn => ({
                        text: btn.textContent.trim(),
                        visible: btn.offsetParent !== null,
                        classes: btn.className
                    }));
                """)

                logger.info(f"📋 Все кнопки в iframe: {all_buttons}")

                self.driver.switch_to.default_content()

            else:
                logger.warning("⚠️ Iframe не найден")

        except Exception as e:
            logger.error(f"❌ Ошибка проверки кнопки Join: {e}")
            self.driver.switch_to.default_content()

        self.analysis_data["join_button_states"].append(state)

        # Создаем скриншот для этого состояния
        screenshot_desc = f"join_check_{context}_{state['join_button_present']}"
        self.take_screenshot(screenshot_desc)

        return state

    def login_as_owner(self):
        """Авторизация под пользователем owner"""
        logger.info("🔐 Авторизация под пользователем owner...")

        try:
            # Переходим на страницу логина
            self.driver.get("http://127.0.0.1:8001/accounts/login/")
            self.take_screenshot("login_page")

            # Заполняем форму
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "login"))
            )
            username_field.clear()
            username_field.send_keys("owner")

            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys("owner123secure")

            self.take_screenshot("login_form_filled")

            # Отправляем форму
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            # Ждем перенаправления
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("127.0.0.1:8001")
            )

            self.take_screenshot("after_login")
            logger.info("✅ Авторизация успешна")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка авторизации: {e}")
            self.take_screenshot("login_error")
            return False

    def analyze_chat_behavior(self):
        """Основной анализ поведения чата"""
        logger.info("🔬 Начало анализа поведения чата...")

        try:
            # Переходим в чат
            self.driver.get("http://127.0.0.1:8001/chat/integrated/")
            self.take_screenshot("chat_initial_load")

            # Ждем загрузки
            time.sleep(5)
            self.collect_console_logs()

            # Серия проверок с интервалами
            for i in range(10):  # 10 проверок с интервалом 10 секунд
                logger.info(f"🔄 Проверка #{i+1}/10")

                state = self.check_join_button_state(f"check_{i+1}")

                if state["join_button_present"]:
                    logger.warning(f"⚠️ Кнопка Join найдена в проверке #{i+1}")
                else:
                    logger.info(f"✅ Кнопка Join отсутствует в проверке #{i+1}")

                # Переключение между каналами для провокации
                if i % 3 == 0 and i > 0:
                    self.test_channel_switching()

                # Обновление страницы каждые 3 проверки
                if i % 3 == 2:
                    logger.info("🔄 Обновление страницы...")
                    self.driver.refresh()
                    time.sleep(3)
                    self.take_screenshot(f"after_refresh_{i+1}")

                self.collect_console_logs()
                time.sleep(10)  # Ждем 10 секунд между проверками

            logger.info("✅ Анализ завершен")

        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            self.analysis_data["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "context": "analyze_chat_behavior"
            })

    def test_channel_switching(self):
        """Тестирование переключения каналов"""
        logger.info("🔀 Тестирование переключения каналов...")

        try:
            # Ищем кнопки переключения каналов
            general_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-channel='general']")
            vip_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-channel='vip']")

            # Переключение на VIP
            logger.info("📡 Переключение на VIP канал...")
            vip_btn.click()
            time.sleep(3)
            self.check_join_button_state("after_vip_switch")

            # Возврат на общий
            logger.info("📡 Возврат на общий канал...")
            general_btn.click()
            time.sleep(3)
            self.check_join_button_state("after_general_switch")

        except Exception as e:
            logger.error(f"❌ Ошибка переключения каналов: {e}")

    def save_analysis_report(self):
        """Сохранение детального отчета анализа"""
        self.analysis_data["end_time"] = datetime.now().isoformat()

        report_file = f"tests/logs/join_button_analysis_report_{self.timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 Отчет сохранен: {report_file}")

        # Создаем краткий отчет
        summary = {
            "total_checks": len(self.analysis_data["join_button_states"]),
            "join_button_appeared": sum(1 for state in self.analysis_data["join_button_states"] if state["join_button_present"]),
            "screenshots_taken": len(self.analysis_data["screenshots"]),
            "console_errors": len([log for log in self.analysis_data["console_logs"] if log["level"] == "SEVERE"]),
            "analysis_duration": self.analysis_data["end_time"]
        }

        logger.info(f"📊 КРАТКАЯ СВОДКА:")
        logger.info(f"   - Всего проверок: {summary['total_checks']}")
        logger.info(f"   - Появлений кнопки Join: {summary['join_button_appeared']}")
        logger.info(f"   - Скриншотов: {summary['screenshots_taken']}")
        logger.info(f"   - Ошибок консоли: {summary['console_errors']}")

        return report_file

    def run_full_analysis(self):
        """Запуск полного анализа"""
        logger.info("🚀 НАЧАЛО ДЕТАЛЬНОГО АНАЛИЗА КНОПКИ JOIN CHANNEL")
        logger.info("=" * 80)

        try:
            # Настройка драйвера
            if not self.setup_driver():
                return False

            # Авторизация
            if not self.login_as_owner():
                return False

            # Основной анализ
            self.analyze_chat_behavior()

            # Сохранение отчета
            report_file = self.save_analysis_report()

            logger.info("=" * 80)
            logger.info("✅ АНАЛИЗ ЗАВЕРШЕН УСПЕШНО")
            logger.info(f"📁 Папка со скриншотами: {self.screenshots_dir}")
            logger.info(f"📄 Файл отчета: {report_file}")

            return True

        except Exception as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА АНАЛИЗА: {e}")
            return False
        finally:
            if self.driver:
                input("Нажмите Enter чтобы закрыть браузер и завершить анализ...")
                self.driver.quit()

def main():
    """Главная функция"""
    analyzer = JoinButtonAnalyzer()
    success = analyzer.run_full_analysis()

    if success:
        print("✅ Анализ завершен успешно")
    else:
        print("❌ Анализ завершен с ошибками")

if __name__ == "__main__":
    main()
