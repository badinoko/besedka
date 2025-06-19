#!/usr/bin/env python3
"""
SELENIUM ТЕСТ - сам нажимаю на OAuth кнопку 30 раз!
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
import base64

def main():
    print("🤖 САМ НАЖИМАЮ НА КНОПКУ 30 РАЗ!")
    print("=" * 50)

    chrome_options = Options()
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)

        for attempt in range(30):
            print(f"\n🔄 ПОПЫТКА {attempt + 1}/30")

            # Открываем Rocket.Chat
            driver.get("http://127.0.0.1:3000")
            time.sleep(2)

            # Ищем кнопку
            buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Sign in with Besedka')]")

            if not buttons:
                print("❌ Кнопка не найдена")
                continue

            main_btn = None
            for btn in buttons:
                if "Custom" not in btn.text:
                    main_btn = btn
                    break

            if not main_btn:
                print("❌ Основная кнопка не найдена")
                continue

            print(f"   Нашел кнопку: {main_btn.text}")

            # Сохраняем текущие окна
            windows_before = len(driver.window_handles)
            url_before = driver.current_url

            # НАЖИМАЕМ!
            main_btn.click()
            time.sleep(3)

            # Проверяем результат
            windows_after = len(driver.window_handles)
            url_after = driver.current_url

            print(f"   Окон до: {windows_before}, после: {windows_after}")
            print(f"   URL до: {url_before}")
            print(f"   URL после: {url_after}")

            if "127.0.0.1:8001" in url_after:
                print("🎉 УСПЕХ! REDIRECT РАБОТАЕТ!")
                return True
            elif windows_after > windows_before:
                print("⚠️  Новое окно открылось")
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(1)
                new_url = driver.current_url
                print(f"   URL нового окна: {new_url}")
                if "127.0.0.1:8001" in new_url:
                    print("🎉 УСПЕХ! POPUP REDIRECT РАБОТАЕТ!")
                    return True
                else:
                    print("❌ Неправильный URL в новом окне")
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
            else:
                print("❌ Ничего не произошло")

            time.sleep(1)

        print("\n💥 ВСЕ 30 ПОПЫТОК ПРОВАЛИЛИСЬ!")
        return False

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
