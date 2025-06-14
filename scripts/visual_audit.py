import os
import time
import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException

# -------------------------------------------------------------
# НАСТРОЙКИ
# -------------------------------------------------------------
BASE_URL = os.getenv("BESEDKA_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
OUTPUT_DIR = Path("audit_screenshots")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = OUTPUT_DIR / "visual_audit_log.json"

USERS = {
    "owner": {"username": "owner", "password": "owner123secure"},
    "moderator": {"username": "admin", "password": "admin123secure"},
    "store_owner": {"username": "store_owner", "password": "storeowner123secure"},
    "store_admin": {"username": "store_admin", "password": "storeadmin123secure"},
    "user": {"username": "test_user", "password": "user123secure"},
}

COMMON_PAGES = [
    ("news_home", "/news/"),
    ("gallery_home", "/gallery/"),
    ("growlogs_home", "/growlogs/"),
    ("store_home", "/store/"),
]

ROLE_SPECIFIC_PAGES = {
    "owner": [
        ("owner_admin", "/owner_admin/"),
    ],
    "moderator": [
        ("moderator_admin", "/moderator_admin/"),
    ],
    "store_owner": [
        ("store_owner_admin", "/store_owner_admin/"),
    ],
    "store_admin": [
        ("store_admin", "/store_admin/"),
    ],
    "user": [],
}


# -------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# -------------------------------------------------------------

def create_driver():
    options = webdriver.ChromeOptions()
    # Убираем headless, чтобы браузер реально открывался (медленнее, но наглядно)
    # options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    # Chrome 137 требует явно включать автоматические разрешения
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver


def login(driver, username: str, password: str):
    driver.get(f"{BASE_URL}/accounts/logout/")
    driver.get(f"{BASE_URL}/accounts/login/")
    wait = WebDriverWait(driver, 30)
    login_field = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='login'], input[name='username']"))
    )
    login_field.clear()
    login_field.send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    # Ждём редирект либо наличие навбара
    wait.until(lambda d: "/accounts/login" not in d.current_url)



def capture_page(driver, role: str, page_key: str, url: str, log):
    record = {"role": role, "page": page_key, "url": url}
    start = time.time()
    try:
        driver.get(f"{BASE_URL}{url}")
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        # небольшая пауза на финальный отрисовку/анимацию
        time.sleep(1.5)
        filename = OUTPUT_DIR / f"{role}_{page_key}.png"
        driver.save_screenshot(str(filename))
        record.update({
            "status": "success",
            "load_time_sec": round(time.time() - start, 2),
            "screenshot": str(filename.relative_to(OUTPUT_DIR)),
        })
    except TimeoutException:
        record.update({
            "status": "timeout",
            "load_time_sec": round(time.time() - start, 2),
        })
    except Exception as exc:
        record.update({
            "status": "error",
            "error": str(exc),
            "load_time_sec": round(time.time() - start, 2),
        })
    log.append(record)


# -------------------------------------------------------------
# ОСНОВНОЙ ПРОЦЕСС
# -------------------------------------------------------------

def main():
    overall_log = []
    for role, creds in USERS.items():
        driver = create_driver()
        try:
            login(driver, creds["username"], creds["password"])
            # Общие страницы
            for key, url in COMMON_PAGES:
                capture_page(driver, role, key, url, overall_log)
            # Специфичные
            for key, url in ROLE_SPECIFIC_PAGES.get(role, []):
                capture_page(driver, role, key, url, overall_log)
        finally:
            driver.quit()
    # Сохраняем лог
    with LOG_FILE.open("w", encoding="utf-8") as fh:
        json.dump(overall_log, fh, ensure_ascii=False, indent=2)
    print(f"\n✅ Аудит завершён. Скриншоты и лог сохранены в {OUTPUT_DIR}\n")


if __name__ == "__main__":
    main()
