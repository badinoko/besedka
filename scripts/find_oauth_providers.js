#!/usr//bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для автоматического прохождения первоначальной настройки Rocket.Chat.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

ADMIN_FULLNAME = "RUSLAN IRUGOV"
ADMIN_USERNAME = "owner"
ADMIN_EMAIL = "badinoko07@gmail.com"
ADMIN_PASSWORD = "BesedkaAdminPassword2025!" # Надежный пароль
ORG_NAME = "Besedka"
ORG_TYPE = "Community"
ORG_SIZE = "1-50"
ORG_COUNTRY = "Russia"

def setup_rocketchat():
    print("🚀 Автоматическая настройка Rocket.Chat...")

    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,1024')

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    os.makedirs("screenshots", exist_ok=True)

    try:
        print("📌 1/5: Открываю http://127.0.0.1:3000")
        driver.get("http://127.0.0.1:3000")

        # --- Шаг 1: Информация об администраторе ---
        print("📝 2/5: Заполняю информацию об администраторе...")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='name']"))).send_keys(ADMIN_FULLNAME)
        driver.find_element(By.CSS_SELECTOR, "input[name='username']").send_keys(ADMIN_USERNAME)
        driver.find_element(By.CSS_SELECTOR, "input[name='email']").send_keys(ADMIN_EMAIL)
        driver.find_element(By.CSS_SELECTOR, "input[name='pass']").send_keys(ADMIN_PASSWORD)
        driver.save_screenshot("screenshots/setup_01_admin_info.png")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        print("✅ Шаг 1 пройден.")

        # --- Шаг 2: Информация об организации ---
        print("🏢 3/5: Заполняю информацию об организации...")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='organization-name']"))).send_keys(ORG_NAME)

        # Выбор типа организации (Community)
        driver.find_element(By.CSS_SELECTOR, "input[name='organization-type']").click()
        wait.until(EC.visibility_of_element_located((By.XPATH, f"//div[contains(text(), '{ORG_TYPE}')]"))).click()

        # Выбор размера (1-50)
        driver.find_element(By.CSS_SELECTOR, "input[name='organization-size']").click()
        wait.until(EC.visibility_of_element_located((By.XPATH, f"//div[contains(text(), '{ORG_SIZE}')]"))).click()

        # Выбор страны (Russia)
        driver.find_element(By.CSS_SELECTOR, "input[name='country']").click()
        wait.until(EC.visibility_of_element_located((By.XPATH, f"//div[contains(text(), '{ORG_COUNTRY}')]"))).click()

        driver.save_screenshot("screenshots/setup_02_org_info.png")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        print("✅ Шаг 2 пройден.")

        # --- Шаг 3: Информация о сайте ---
        print("🌐 4/5: Заполняю информацию о сайте...")
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='site-name']"))).clear()
        driver.find_element(By.CSS_SELECTOR, "input[name='site-name']").send_keys(ORG_NAME)

        # Выбор языка (Русский)
        driver.find_element(By.CSS_SELECTOR, "input[name='language']").click()
        wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), 'Русский')]"))).click()

        driver.save_screenshot("screenshots/setup_03_site_info.png")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        print("✅ Шаг 3 пройден.")

        # --- Шаг 4: Регистрация сервера ---
        print("☁️ 5/5: Пропускаю регистрацию сервера...")
        wait.until(EC.visibility_of_element_located((By.XPATH, "//button[contains(text(), 'Продолжить автономно')]"))).click()
        print("✅ Шаг 4 пройден.")

        # --- Финальная проверка ---
        print("🎉 Настройка завершена! Ожидание главной страницы...")
        wait.until(EC.visibility_of_element_located((By.ID, "rocket-chat")))
        time.sleep(3) # Даем время на прогрузку интерфейса
        driver.save_screenshot("screenshots/setup_04_final_workspace.png")
        print("🖥️ Рабочее пространство готово.")

    except Exception as e:
        print(f"\n❌ ОШИБКА НАСТРОЙКИ: {e}")
        driver.save_screenshot("screenshots/setup_error.png")

    finally:
        driver.quit()
        print("\n🏁 Скрипт настройки завершен.")

if __name__ == "__main__":
    setup_rocketchat()
