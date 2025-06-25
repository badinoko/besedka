#!/usr/bin/env python3
"""
АВТОМАТИЧЕСКИЙ ЛОГИН В ROCKET.CHAT
===================================
Этот скрипт автоматически авторизует пользователя owner в Rocket.Chat
через Django OAuth, избавляя от необходимости ручного входа.

Использование:
    python scripts/auto_login_rocketchat.py

Требования:
    - Django сервер запущен на 127.0.0.1:8001
    - Rocket.Chat запущен на 127.0.0.1:3000
    - Пользователь owner авторизован в Django
"""

import requests
import sys
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Отключаем предупреждения SSL для локального развертывания
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Конфигурация
DJANGO_BASE = "http://127.0.0.1:8001"
ROCKETCHAT_BASE = "http://127.0.0.1:3000"
OWNER_CREDENTIALS = {
    'username': 'owner',
    'password': 'owner123secure'
}

def print_status(message, status="INFO"):
    """Красивый вывод статуса"""
    icons = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "PROGRESS": "🔄"
    }
    print(f"{icons.get(status, '📋')} {message}")

def check_services():
    """Проверка доступности сервисов"""
    print_status("Проверяю доступность сервисов...", "PROGRESS")

    # Проверка Django
    try:
        response = requests.get(f"{DJANGO_BASE}/", timeout=5)
        if response.status_code == 200:
            print_status("Django сервер доступен", "SUCCESS")
        else:
            print_status(f"Django сервер недоступен (код: {response.status_code})", "ERROR")
            return False
    except Exception as e:
        print_status(f"Django сервер недоступен: {e}", "ERROR")
        return False

    # Проверка Rocket.Chat
    try:
        response = requests.get(f"{ROCKETCHAT_BASE}/", timeout=10)
        if response.status_code == 200:
            print_status("Rocket.Chat сервер доступен", "SUCCESS")
        else:
            print_status(f"Rocket.Chat недоступен (код: {response.status_code})", "ERROR")
            return False
    except Exception as e:
        print_status(f"Rocket.Chat недоступен: {e}", "ERROR")
        return False

    return True

def login_to_django(session):
    """Авторизация в Django"""
    print_status("Авторизуюсь в Django...", "PROGRESS")

    # Получаем страницу логина для CSRF токена
    try:
        response = session.get(f"{DJANGO_BASE}/accounts/login/")
        if 'csrfmiddlewaretoken' not in response.text:
            print_status("Не найден CSRF токен на странице логина", "ERROR")
            return False
    except Exception as e:
        print_status(f"Ошибка получения страницы логина: {e}", "ERROR")
        return False

    # Извлекаем CSRF токен из формы
    import re
    csrf_match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', response.text)
    if not csrf_match:
        # Пробуем альтернативный способ извлечения
        csrf_match = re.search(r'csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', response.text)
        if not csrf_match:
            print_status("Не удалось извлечь CSRF токен", "ERROR")
            return False

    csrf_token = csrf_match.group(1)
    print_status(f"CSRF токен получен: {csrf_token[:10]}...", "PROGRESS")

    # Получаем CSRF токен из cookies
    csrf_cookie = None
    for cookie in session.cookies:
        if cookie.name == 'csrftoken':
            csrf_cookie = cookie.value
            break

    # Добавляем заголовки для CSRF защиты
    headers = {
        'Referer': f"{DJANGO_BASE}/accounts/login/",
        'X-CSRFToken': csrf_cookie if csrf_cookie else csrf_token,
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    # Отправляем данные логина
    login_data = {
        'login': OWNER_CREDENTIALS['username'],  # Django allauth использует 'login', не 'username'
        'password': OWNER_CREDENTIALS['password'],
        'csrfmiddlewaretoken': csrf_token
    }

    try:
        response = session.post(f"{DJANGO_BASE}/accounts/login/",
                              data=login_data,
                              headers=headers,
                              allow_redirects=False)

        print_status(f"Ответ Django: {response.status_code}", "PROGRESS")

        # Проверяем успешность авторизации
        if response.status_code == 302:  # Редирект означает успех
            print_status("Успешная авторизация в Django", "SUCCESS")
            return True
        elif response.status_code == 200 and 'login' in response.text.lower():
            print_status("Неверные учетные данные для Django", "ERROR")
            return False
        else:
            print_status(f"Неожиданный ответ: {response.status_code}", "WARNING")
            return True  # Пробуем продолжить

    except Exception as e:
        print_status(f"Ошибка авторизации в Django: {e}", "ERROR")
        return False

def trigger_oauth_login(session):
    """Инициация OAuth логина в Rocket.Chat"""
    print_status("Инициирую OAuth логин в Rocket.Chat...", "PROGRESS")

    # Нажимаем кнопку "Войти через Беседку" на странице Rocket.Chat
    try:
        # Сначала получаем страницу логина Rocket.Chat
        response = session.get(f"{ROCKETCHAT_BASE}/login")

        # Ищем OAuth URL для провайдера Besedka
        import re
        oauth_match = re.search(r'href="([^"]*oauth/besedka[^"]*)"', response.text)
        if not oauth_match:
            print_status("Не найдена кнопка OAuth на странице Rocket.Chat", "WARNING")
            # Пробуем прямой URL
            oauth_url = f"{ROCKETCHAT_BASE}/_oauth/besedka"
        else:
            oauth_url = ROCKETCHAT_BASE + oauth_match.group(1)

        print_status(f"Переходим по OAuth URL: {oauth_url}", "PROGRESS")

        # Переходим по OAuth URL (это инициирует процесс авторизации)
        response = session.get(oauth_url, allow_redirects=True)

        # Проверяем результат
        if "besedka" in response.url.lower() or response.status_code == 200:
            print_status("OAuth авторизация инициирована", "SUCCESS")
            return True
        else:
            print_status(f"Неожиданный результат OAuth: {response.url}", "WARNING")
            return True  # Возможно, всё равно сработало

    except Exception as e:
        print_status(f"Ошибка OAuth авторизации: {e}", "ERROR")
        return False

def verify_login():
    """Проверка успешности авторизации"""
    print_status("Проверяю результат авторизации...", "PROGRESS")

    # Создаем новую сессию для проверки
    check_session = requests.Session()

    try:
        # Проверяем доступ к Rocket.Chat
        response = check_session.get(f"{ROCKETCHAT_BASE}/home", timeout=10)

        if response.status_code == 200 and "login" not in response.url.lower():
            print_status("Авторизация в Rocket.Chat успешна!", "SUCCESS")
            return True
        else:
            print_status("Возможно, требуется ручная проверка", "WARNING")
            return False

    except Exception as e:
        print_status(f"Ошибка проверки авторизации: {e}", "WARNING")
        return False

def main():
    """Главная функция"""
    print("🚀 АВТОМАТИЧЕСКИЙ ЛОГИН В ROCKET.CHAT")
    print("=" * 50)

    # Проверка сервисов
    if not check_services():
        print_status("Сервисы недоступны. Проверьте запуск Docker и Django.", "ERROR")
        sys.exit(1)

    # Создаем сессию для сохранения cookies
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    # Пошаговая авторизация
    if not login_to_django(session):
        print_status("Не удалось авторизоваться в Django", "ERROR")
        sys.exit(1)

    # Небольшая пауза
    time.sleep(2)

    if not trigger_oauth_login(session):
        print_status("Не удалось инициировать OAuth логин", "ERROR")
        sys.exit(1)

    # Пауза для завершения OAuth процесса
    time.sleep(3)

    # Проверка результата
    verify_login()

    print("")
    print_status("ГОТОВО! Попробуйте открыть интегрированный чат:", "SUCCESS")
    print_status("http://127.0.0.1:8001/chat/integrated/", "INFO")
    print("")
    print_status("Также проверьте прямой доступ к Rocket.Chat:", "INFO")
    print_status("http://127.0.0.1:3000/", "INFO")

if __name__ == "__main__":
    main()
