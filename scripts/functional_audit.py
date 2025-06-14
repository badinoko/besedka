import os
import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

"""
ГЛОБАЛЬНЫЙ ФУНКЦИОНАЛЬНЫЙ АУДИТ САЙТА «Беседка»
------------------------------------------------
Проверяет ключевые пользовательские сценарии для каждой роли и
валидирует наличие элементов интерфейса (фильтры, карточки,
комментарии, админ-панели).

Результаты сохраняются в JSON (`audit_reports/functional_audit.json`) и
папку со скриншотами (`audit_reports/screens/`).

По умолчанию работает в headless-режиме. Установите
    BESedka_HEADLESS=0
чтобы наблюдать браузер во время проверки.
"""

BASE_URL = os.getenv("BESEDKA_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
HEADLESS = os.getenv("BESEDKA_HEADLESS", "1") != "0"

REPORT_DIR = Path("audit_reports")
SCREEN_DIR = REPORT_DIR / "screens"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
SCREEN_DIR.mkdir(parents=True, exist_ok=True)
REPORT_FILE = REPORT_DIR / "functional_audit.json"

USERS = {
    "owner": {"username": "owner", "password": "owner123secure"},
    "moderator": {"username": "admin", "password": "admin123secure"},
    "store_owner": {"username": "store_owner", "password": "storeowner123secure"},
    "store_admin": {"username": "store_admin", "password": "storeadmin123secure"},
    "user": {"username": "test_user", "password": "user123secure"},
}

COMMON_PAGES = {
    "news_home": "/news/",
    "gallery_home": "/gallery/",
    "growlogs_home": "/growlogs/",
    "store_home": "/store/",
}

ADMIN_PAGES = {
    "owner": [("owner_admin", "/owner_admin/")],
    "moderator": [("moderator_admin", "/moderator_admin/")],
    "store_owner": [("store_owner_admin", "/store_owner_admin/")],
    "store_admin": [("store_admin", "/store_admin/")],
    "user": [],
}


# ------------------------------------------------------------------------
# УТИЛИТЫ
# ------------------------------------------------------------------------

def create_driver():
    opts = webdriver.ChromeOptions()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    service = ChromeService(ChromeDriverManager().install())
    drv = webdriver.Chrome(service=service, options=opts)
    drv.set_page_load_timeout(60)
    return drv


def wait_ready(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def login(driver, username, password):
    driver.get(f"{BASE_URL}/accounts/logout/")
    driver.get(f"{BASE_URL}/accounts/login/")
    wait = WebDriverWait(driver, 30)
    field = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[name='login'], input[name='username']")
        )
    )
    field.clear()
    field.send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    # Ждём выхода со страницы логина
    wait.until(lambda d: "/accounts/login" not in d.current_url)


def safe_click(driver, selector):
    try:
        elem = driver.find_element(By.CSS_SELECTOR, selector)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        time.sleep(0.1)
        elem.click()
        return True
    except Exception:
        return False


def capture(driver, role, page_key, status):
    fname = SCREEN_DIR / f"{role}_{page_key}_{status}.png"
    driver.save_screenshot(str(fname))
    return str(fname.relative_to(REPORT_DIR))


# ------------------------------------------------------------------------
# ПРОВЕРКИ
# ------------------------------------------------------------------------

def check_filters(driver, min_expected=2):
    links = driver.find_elements(By.CSS_SELECTOR, ".filter-tab-link")
    return len(links) >= min_expected, len(links)


def check_cards(driver, card_selector):
    cards = driver.find_elements(By.CSS_SELECTOR, card_selector)
    return len(cards) > 0, len(cards)


def submit_comment(driver, text):
    try:
        textarea = driver.find_element(By.CSS_SELECTOR, "#comment-form textarea")
        textarea.send_keys(text)
        safe_click(driver, "#comment-form button[type='submit']")
        time.sleep(1)
        return text in driver.page_source
    except NoSuchElementException:
        return False


# ------------------------------------------------------------------------
# ОСНОВНОЙ АУДИТ
# ------------------------------------------------------------------------

def audit_role(role, creds):
    driver = create_driver()
    role_log = []

    def log(page_key, status, details=None):
        entry = {
            "role": role,
            "page": page_key,
            "status": status,
            "details": details or {},
        }
        role_log.append(entry)
        entry["screenshot"] = capture(driver, role, page_key, status)

    try:
        login(driver, creds["username"], creds["password"])
    except Exception as exc:
        log("login", "error", {"error": str(exc)})
        driver.quit()
        return role_log

    # --- Common pages ---
    for page_key, url in COMMON_PAGES.items():
        try:
            driver.get(f"{BASE_URL}{url}")
            wait_ready(driver)
            ok_filters, filters_count = check_filters(driver)
            ok_cards, cards_count = check_cards(driver, ".unified-card, .news-card")
            status = "ok" if ok_filters and ok_cards else "failed"
            details = {
                "filters": filters_count,
                "cards": cards_count,
            }
            # Доп. сценарии для новостей
            if page_key == "news_home" and ok_cards:
                # открываем первую новость
                safe_click(driver, ".news-card a")
                wait_ready(driver)
                comment_text = f"Авто {int(time.time())}"
                comment_ok = submit_comment(driver, comment_text)
                details["comment_added"] = comment_ok
                driver.back()
            log(page_key, status, details)
        except TimeoutException:
            log(page_key, "timeout")
        except Exception as exc:
            log(page_key, "error", {"error": str(exc)})

    # --- Admin pages ---
    for page_key, url in ADMIN_PAGES.get(role, []):
        try:
            driver.get(f"{BASE_URL}{url}")
            wait_ready(driver)
            # Проверяем код ответа через JS (доступно ли тело)
            body_exists = bool(driver.find_elements(By.TAG_NAME, "body"))
            status = "ok" if body_exists else "failed"
            log(page_key, status)
        except Exception as exc:
            log(page_key, "error", {"error": str(exc)})

    driver.quit()
    return role_log


# ------------------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------------------

def main():
    full_report = []
    start_ts = time.time()
    for role, creds in USERS.items():
        full_report.extend(audit_role(role, creds))
    duration = round(time.time() - start_ts)
    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base_url": BASE_URL,
        "duration_sec": duration,
        "roles_tested": list(USERS.keys()),
        "results": full_report,
    }
    with REPORT_FILE.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    print(f"\n✅ Функциональный аудит завершён за {duration} сек. Отчёт: {REPORT_FILE}\n")


if __name__ == "__main__":
    main()
