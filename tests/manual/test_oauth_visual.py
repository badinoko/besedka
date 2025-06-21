#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os

print("🔍 ЗАПУСК ВИЗУАЛЬНОГО ТЕСТА OAUTH КНОПОК...")

# Настройка Chrome
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')

driver = webdriver.Chrome(options=options)

try:
    # Открываем Rocket.Chat
    print("\n📌 Открываю Rocket.Chat на http://127.0.0.1:3000")
    driver.get("http://127.0.0.1:3000")
    time.sleep(5)

    # Делаем скриншот главной страницы
    os.makedirs("screenshots", exist_ok=True)
    driver.save_screenshot("screenshots/01_main_page.png")
    print("📸 Сохранен скриншот главной страницы")

    # Ищем все OAuth кнопки
    print("\n🔍 Поиск OAuth кнопок...")
    oauth_buttons = driver.find_elements(By.CSS_SELECTOR, "button")

    print(f"\n📊 Найдено всего кнопок: {len(oauth_buttons)}")

    oauth_count = 0
    for i, button in enumerate(oauth_buttons):
        try:
            text = button.text
            if "Sign in with" in text or "besedka" in text.lower() or "custom" in text.lower():
                oauth_count += 1
                print(f"\n  OAuth кнопка {oauth_count}:")
                print(f"    Текст: '{text}'")
                print(f"    Видима: {button.is_displayed()}")
                print(f"    Цвет фона: {button.value_of_css_property('background-color')}")

                # Выделяем кнопку
                driver.execute_script("arguments[0].style.border = '3px solid red';", button)

        except:
            pass

    print(f"\n📊 ИТОГО OAuth кнопок: {oauth_count}")

    # Финальный скриншот
    driver.save_screenshot("screenshots/02_oauth_highlighted.png")
    print("\n📸 Сохранен скриншот с выделенными OAuth кнопками")

except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    driver.save_screenshot("screenshots/error.png")

finally:
    print("\n🏁 Тест завершен")
    driver.quit()
