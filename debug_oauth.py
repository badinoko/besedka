#!/usr/bin/env python3
"""
ОТЛАДКА: Что реально происходит на странице Rocket.Chat?
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

def debug_rocketchat():
    print("🔍 ОТЛАДКА: Что происходит на странице Rocket.Chat?")
    print("=" * 60)

    chrome_options = Options()
    chrome_options.add_argument("--disable-web-security")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)

        print("1. 🌐 Загружаю http://127.0.0.1:3000...")
        driver.get("http://127.0.0.1:3000")
        time.sleep(5)  # Ждем загрузки

        print(f"2. ✅ Текущий URL: {driver.current_url}")
        print(f"3. ✅ Заголовок страницы: {driver.title}")

        # Проверяем что страница загрузилась
        page_source = driver.page_source
        print(f"4. ✅ Размер HTML: {len(page_source)} символов")

        # Ищем любые кнопки
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"5. 🔘 Найдено кнопок: {len(all_buttons)}")

        if all_buttons:
            print("   Текст кнопок:")
            for i, btn in enumerate(all_buttons[:10]):  # Первые 10
                try:
                    text = btn.text.strip()
                    if text:
                        print(f"   - {i+1}. '{text}'")
                except:
                    print(f"   - {i+1}. [нет текста]")

        # Ищем OAuth кнопки
        oauth_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Sign in')]")
        print(f"6. 🔐 OAuth кнопок: {len(oauth_buttons)}")

        if oauth_buttons:
            print("   OAuth кнопки:")
            for i, btn in enumerate(oauth_buttons):
                try:
                    text = btn.text.strip()
                    print(f"   - {i+1}. '{text}'")
                except:
                    print(f"   - {i+1}. [ошибка получения текста]")

        # Ищем по классу или ID
        login_section = driver.find_elements(By.CLASS_NAME, "login")
        print(f"7. 📝 Элементов с классом 'login': {len(login_section)}")

        # Проверяем ошибки в консоли
        try:
            logs = driver.get_log('browser')
            if logs:
                print("8. ❌ Ошибки в консоли:")
                for log in logs[-3:]:  # Последние 3
                    print(f"   {log['level']}: {log['message']}")
            else:
                print("8. ✅ Ошибок в консоли нет")
        except:
            print("8. ⚠️  Не удалось получить логи консоли")

        # Сохраняем скриншот
        try:
            driver.save_screenshot("rocketchat_debug.png")
            print("9. 📸 Скриншот сохранен: rocketchat_debug.png")
        except:
            print("9. ❌ Не удалось сохранить скриншот")

        # Проверяем HTML на наличие OAuth
        if "oauth" in page_source.lower() or "besedka" in page_source.lower():
            print("10. ✅ В HTML есть упоминания OAuth/Besedka")
        else:
            print("10. ❌ В HTML НЕТ упоминаний OAuth/Besedka")

        return True

    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    debug_rocketchat()
