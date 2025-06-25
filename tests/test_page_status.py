#!/usr/bin/env python3
"""
🔍 Автоматический тест HTTP статусов основных страниц
Проверяет что страницы не возвращают 500 ошибок
"""

import requests
import sys
from urllib.parse import urljoin

# Базовые настройки
BASE_URL = "http://127.0.0.1:8001"
TIMEOUT = 10

# Список страниц для тестирования
# 200 = доступна без авторизации
# 302 = требует авторизации (редирект на login)
PAGES_TO_TEST = [
    # Основные страницы
    ('/', 200, 'Главная страница'),
    ('/news/', 200, 'Новости'),
    ('/gallery/', 200, 'Галерея'),
    ('/growlogs/', 200, 'Гроу-репорты'),
    ('/store/', 200, 'Магазин'),

    # Чат (требует авторизации)
    ('/chat/', 302, 'Главная чата'),
    ('/chat/integrated/', 302, 'Интегрированный чат'),
    ('/chat/test/', 302, '🧪 Тестовая страница чата'),

    # Авторизация
    ('/accounts/login/', 200, 'Страница входа'),
]

def test_page_status(url_path, expected_status, description):
    """Тестирует HTTP статус одной страницы"""
    full_url = urljoin(BASE_URL, url_path)

    try:
        response = requests.get(full_url, timeout=TIMEOUT, allow_redirects=False)
        actual_status = response.status_code

        if actual_status == expected_status:
            print(f"✅ {description}: {actual_status} - {url_path}")
            return True
        elif actual_status == 500:
            print(f"❌ {description}: 500 SERVER ERROR - {url_path}")
            return False
        else:
            print(f"⚠️ {description}: {actual_status} (ожидался {expected_status}) - {url_path}")
            return True  # Не критично, если статус отличается но не 500

    except requests.exceptions.ConnectionError:
        print(f"❌ {description}: CONNECTION ERROR - Сервер недоступен - {url_path}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {description}: TIMEOUT - {url_path}")
        return False
    except Exception as e:
        print(f"❌ {description}: ERROR - {str(e)} - {url_path}")
        return False

def main():
    """Запускает тестирование всех страниц"""
    print("🔍 АВТОМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ HTTP СТАТУСОВ")
    print("=" * 60)

    success_count = 0
    total_count = len(PAGES_TO_TEST)

    for url_path, expected_status, description in PAGES_TO_TEST:
        if test_page_status(url_path, expected_status, description):
            success_count += 1

    print("=" * 60)
    print(f"📊 РЕЗУЛЬТАТ: {success_count}/{total_count} страниц прошли тест")

    if success_count == total_count:
        print("🎉 ВСЕ СТРАНИЦЫ РАБОТАЮТ КОРРЕКТНО!")
        return 0
    else:
        failed_count = total_count - success_count
        print(f"⚠️ {failed_count} страниц имеют проблемы")
        return 1

if __name__ == "__main__":
    sys.exit(main())
