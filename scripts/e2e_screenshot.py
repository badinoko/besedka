import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "http://127.0.0.1:8001"
SCREEN_DIR = Path("audit_screenshots/full_audit")
SCREEN_DIR.mkdir(parents=True, exist_ok=True)

CSV_LOG = Path("audit_reports/e2e_results.csv")
CSV_LOG.parent.mkdir(parents=True, exist_ok=True)
if not CSV_LOG.exists():
    CSV_LOG.write_text("role,step,status,screenshot\n", encoding="utf-8")

ROLES = {
    "owner": {
        "username": "owner",
        "password": "owner123secure",
        "pages": ["/owner_admin/", "/moderator_admin/"]
    },
    "admin": {
        "username": "admin",
        "password": "admin123secure",
        "pages": ["/moderator_admin/"]
    },
    "store_owner": {
        "username": "store_owner",
        "password": "storeowner123secure",
        "pages": ["/store_owner_admin/"]
    },
    "store_admin": {
        "username": "store_admin",
        "password": "storeadmin123secure",
        "pages": ["/store_admin/"]
    },
    "user": {
        "username": "test_user",
        "password": "user123secure",
        "pages": ["/store/", "/gallery/", "/growlogs/", "/news/"]
    },
    "guest": {
        "username": None,
        "password": None,
        "pages": ["/store/", "/gallery/", "/chat/"]
    },
}


def save_screenshot(driver: webdriver.Chrome, name: str):
    path = SCREEN_DIR / f"{name}.png"
    driver.save_screenshot(str(path))
    print(f"Screenshot saved: {path}")


def login(driver: webdriver.Chrome, username: str, password: str):
    # Гостевой режим – без авторизации
    if not username:
        return

    driver.get(f"{BASE_URL}/accounts/login/")
    time.sleep(1)
    # Поля формы логина (allauth)
    try:
        driver.find_element(By.ID, "id_username").send_keys(username)
    except Exception:
        driver.find_element(By.ID, "id_login").send_keys(username)
    driver.find_element(By.ID, "id_password").send_keys(password)
    driver.find_element(By.ID, "id_password").send_keys(Keys.RETURN)
    time.sleep(2)
    save_screenshot(driver, f"{username}_dashboard")


def log(role, step, status, shot):
    CSV_LOG.write_text(f"{role},{step},{status},{shot}\n", encoding="utf-8", append=True)


def user_store_flow(driver):
    """Добавление товара в корзину и checkout для test_user"""
    driver.get(f"{BASE_URL}/store/")
    time.sleep(2)
    # клик по первой карточке сорта
    try:
        first_card = driver.find_element(By.CSS_SELECTOR, "a.card-link, a.card")
        first_card.click()
        time.sleep(2)
        save_screenshot(driver, "user_product_detail")
        # Добавить первую форму в корзину
        add_btn = driver.find_element(By.CSS_SELECTOR, "form button[type=submit]")
        add_btn.click()
        time.sleep(2)
        save_screenshot(driver, "user_added_to_cart")
        driver.get(f"{BASE_URL}/store/cart/")
        time.sleep(2)
        save_screenshot(driver, "user_cart")
        # checkout
        driver.get(f"{BASE_URL}/store/checkout/")
        time.sleep(2)
        btn = driver.find_element(By.CSS_SELECTOR, "button[type=submit]")
        btn.click()
        time.sleep(2)
        save_screenshot(driver, "user_checkout_success")
    except Exception as e:
        print("User store flow error", e)


def guest_restrictions(driver):
    driver.get(f"{BASE_URL}/gallery/")
    time.sleep(2)
    try:
        like_btn = driver.find_element(By.CSS_SELECTOR, ".like-btn, .fa-heart")
        like_btn.click()
        time.sleep(2)
        save_screenshot(driver, "guest_like_redirect")
    except Exception:
        pass
    driver.get(f"{BASE_URL}/chat/")
    time.sleep(2)
    try:
        msg_input = driver.find_element(By.CSS_SELECTOR, "#chat-input")
        msg_input.send_keys("Hi")
        msg_input.send_keys(Keys.RETURN)
        time.sleep(2)
        save_screenshot(driver, "guest_chat_restrict")
    except Exception:
        pass


def main():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # uncomment if headless desired
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        for role, data in ROLES.items():
            print(f"Testing role: {role}")
            login(driver, data["username"], data["password"])
            for page in data["pages"]:
                driver.get(f"{BASE_URL}{page}")
                time.sleep(2)
                save_screenshot(driver, f"{data['username']}_{page.strip('/').replace('/', '_') or 'home'}")
            if role == "user":
                user_store_flow(driver)
            if role == "guest":
                guest_restrictions(driver)
                continue  # no logout for guest
            # Logout to prepare for next user
            driver.get(f"{BASE_URL}/accounts/logout/")
            time.sleep(1)
            try:
                driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
            except Exception:
                pass
            time.sleep(1)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
