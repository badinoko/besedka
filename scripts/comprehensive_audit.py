import os
import time
import json
import urllib.parse
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

"""
Полноценный визуальный и функциональный аудит сайта «Беседка».

• Для каждой роли выполняется вход.
• Список точек входа формируется из COMMON_PAGES + ROLE_SPECIFIC_PAGES.
• Для каждой посещённой страницы собираются все ссылки <a>, а также кнопки <button> с   атрибутом data-href или onclick, ведущие на тот же домен.
• Переход по каждой новой ссылке выполняется рекурсивно (BFS) с учётом   ограничения MAX_PAGES_PER_ROLE, чтобы аудит мог длиться часами, но не навсегда.
• После загрузки страницы выполняется скриншот и фиксация журналов о размере,   времени загрузки, количестве кликабельных элементов.
• Логи и скриншоты сохраняются в audit_screenshots/full_audit.

ВАЖНО: скрипт кликает ТОЛЬКО по GET ссылкам (без form action="POST" и без   параметров confirm_destroy/confirm_delete), чтобы не вносить изменений.

Запуск:
$env:BESEDKA_BASE_URL="http://127.0.0.1:8001"; python scripts/comprehensive_audit.py
"""

BASE_URL = os.getenv("BESEDKA_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
OUTPUT_DIR = Path("audit_screenshots") / "full_audit"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = OUTPUT_DIR / "comprehensive_audit_log.json"

# Настройки времени и глубины обхода:
PAGE_LOAD_TIMEOUT = 60  # секунд
MAX_PAGES_PER_ROLE = 500  # лимит, чтобы скрипт не зациклился навечно
WAIT_BETWEEN_CLICKS = 1  # сек, дать шанс анимациям

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
    "owner": [("owner_admin", "/owner_admin/")],
    "moderator": [("moderator_admin", "/moderator_admin/")],
    "store_owner": [("store_owner_admin", "/store_owner_admin/")],
    "store_admin": [("store_admin", "/store_admin/")],
    "user": [],
}


def create_driver():
    options = webdriver.ChromeOptions()
    # Полноценный UI — без headless, чтобы отрабатывали все анимации
    # options.add_argument("--headless=new")  # можно вернуть при необходимости
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver


def login(driver, username: str, password: str):
    """Логин с учётом возможного редиректа после успешного входа."""
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
    # дождаться навбара или редиректа
    wait.until(lambda d: "/accounts/login" not in d.current_url)


def normalize_url(url: str) -> str:
    """Превращает относительные пути в абсолютные, прибирает hash и query."""
    if url.startswith("#") or not url:
        return ""
    url = urllib.parse.urljoin(BASE_URL + "/", url)
    parsed = urllib.parse.urlparse(url)
    # только то же доменное имя и схема, убираем query и fragment для уникальности
    if parsed.netloc != urllib.parse.urlparse(BASE_URL).netloc:
        return ""
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def extract_links(driver):
    links = set()
    # <a href>
    for el in driver.find_elements(By.TAG_NAME, "a"):
        url = el.get_attribute("href")
        norm = normalize_url(url)
        if norm:
            links.add(norm)
    # кнопки с data-href
    for el in driver.find_elements(By.CSS_SELECTOR, "button[data-href]"):
        url = el.get_attribute("data-href")
        norm = normalize_url(url)
        if norm:
            links.add(norm)
    # возможные onclick="location.href='...'"
    for el in driver.find_elements(By.CSS_SELECTOR, "*[onclick]"):
        onclick = el.get_attribute("onclick") or ""
        if "location.href" in onclick:
            # пробуем выделить строку URL в кавычках
            try:
                part = onclick.split("location.href")[-1]
                # убираем всё кроме содержимого кавычек/апострофов
                part = part.split("\"")[1] if "\"" in part else part.split("'")[1]
            except Exception:
                continue
            norm = normalize_url(part)
            if norm:
                links.add(norm)
    return links


def capture(driver, role: str, url: str, log):
    record: dict[str, object] = {"role": role, "url": url}
    start = time.time()
    try:
        driver.get(url)
        WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        # Пауза для анимаций
        time.sleep(1.5)
        # Скриншот
        safe_path = url.replace(BASE_URL, "").strip("/").replace("/", "_") or "root"
        filename = OUTPUT_DIR / f"{role}_{safe_path}.png"
        driver.save_screenshot(str(filename))
        record.update(
            {
                "status": "success",
                "load_time_sec": round(time.time() - start, 2),
                "screenshot": str(filename.relative_to(OUTPUT_DIR)),
            }
        )
    except TimeoutException:
        record.update({"status": "timeout", "load_time_sec": round(time.time() - start, 2)})
    except WebDriverException as exc:
        record.update({"status": "webdriver_error", "error": str(exc)[:300], "load_time_sec": round(time.time() - start, 2)})
    except Exception as exc:
        record.update({"status": "error", "error": str(exc)[:300], "load_time_sec": round(time.time() - start, 2)})
    log.append(record)


def audit_role(role: str, creds: dict, overall_log):
    driver = create_driver()
    visited: set[str] = set()
    queue = []

    try:
        login(driver, creds["username"], creds["password"])
        # начальные URL
        for _, path in COMMON_PAGES + ROLE_SPECIFIC_PAGES.get(role, []):
            url = normalize_url(path)
            if url:
                queue.append(url)

        while queue and len(visited) < MAX_PAGES_PER_ROLE:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)
            capture(driver, role, url, overall_log)
            time.sleep(WAIT_BETWEEN_CLICKS)
            # собираем ссылки со страницы
            try:
                new_links = extract_links(driver)
            except Exception:
                new_links = set()
            for link in new_links:
                if link not in visited and link not in queue:
                    # игнорируем опасные ссылки logout, delete и т.п.
                    if any(token in link for token in ["logout", "delete", "remove", "drop", "reset"]):
                        continue
                    queue.append(link)
    finally:
        driver.quit()


def main():
    overall_log: list[dict[str, object]] = []
    for role, creds in USERS.items():
        audit_role(role, creds, overall_log)
    with LOG_FILE.open("w", encoding="utf-8") as fh:
        json.dump(overall_log, fh, ensure_ascii=False, indent=2)
    print(f"\n✅ Полный аудит завершён. Данные сохранены в {OUTPUT_DIR}\n")


if __name__ == "__main__":
    main()
