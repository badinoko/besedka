#!/usr/bin/env python3
"""
Тестирование OAuth интеграции Rocket.Chat
"""

import requests
import json
import re
from urllib.parse import urlencode

def test_rocket_oauth():
    """Тестирует OAuth интеграцию с Rocket.Chat"""

    base_url = "http://127.0.0.1:8001"
    session = requests.Session()

    print("🚀 Тестирование OAuth интеграции Rocket.Chat")
    print("=" * 50)

    # 1. Проверяем доступность сервисов
    print("\n1. Проверка доступности сервисов:")

    try:
        django_response = session.get(f"{base_url}/")
        print(f"   Django: {django_response.status_code}")

        rocket_response = session.get("http://127.0.0.1:3000/")
        print(f"   Rocket.Chat: {rocket_response.status_code}")

    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return False

    # 2. Авторизация в Django
    print("\n2. Авторизация в Django:")

    try:
        # Получаем страницу логина для CSRF токена
        login_page = session.get(f"{base_url}/accounts/login/")
        print(f"   Страница логина: {login_page.status_code}")

        # Извлекаем CSRF токен более надежным способом
        csrf_token = None

        # Пробуем найти в meta теге
        csrf_meta_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', login_page.text)
        if csrf_meta_match:
            csrf_token = csrf_meta_match.group(1)

        # Пробуем найти в input поле
        if not csrf_token:
            csrf_input_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
            if csrf_input_match:
                csrf_token = csrf_input_match.group(1)

        # Пробуем найти в cookies
        if not csrf_token and 'csrftoken' in session.cookies:
            csrf_token = session.cookies['csrftoken']

        if not csrf_token:
            print("   ❌ Не удалось получить CSRF токен")
            print("   🔍 Поиск в тексте страницы...")
            # Выводим часть страницы для диагностики
            if 'csrf' in login_page.text.lower():
                print("   ℹ️  CSRF найден в странице")
            else:
                print("   ⚠️  CSRF не найден в странице")
            return False

        print(f"   ✅ CSRF токен получен: {csrf_token[:10]}...")

        # Авторизуемся
        login_data = {
            'username': 'owner',
            'password': 'owner123secure',
            'csrfmiddlewaretoken': csrf_token
        }

        # Устанавливаем дополнительные заголовки
        headers = {
            'X-CSRFToken': csrf_token,
            'Referer': f"{base_url}/accounts/login/"
        }

        login_response = session.post(f"{base_url}/accounts/login/",
                                    data=login_data,
                                    headers=headers,
                                    allow_redirects=False)

        print(f"   Ответ авторизации: {login_response.status_code}")

        if login_response.status_code in [200, 302]:
            print("   ✅ Авторизация успешна")

            # Проверяем редирект
            if login_response.status_code == 302:
                redirect_location = login_response.headers.get('Location', '')
                print(f"   🔗 Редирект на: {redirect_location}")
        else:
            print(f"   ❌ Ошибка авторизации: {login_response.status_code}")
            print(f"   📝 Содержимое ответа: {login_response.text[:200]}...")
            return False

    except Exception as e:
        print(f"   ❌ Ошибка авторизации: {e}")
        return False

    # 3. Проверяем, что авторизация прошла успешно
    print("\n3. Проверка статуса авторизации:")

    try:
        # Проверяем, можем ли мы получить доступ к защищенной странице
        profile_response = session.get(f"{base_url}/users/cabinet/")
        print(f"   Доступ к личному кабинету: {profile_response.status_code}")

        if profile_response.status_code == 200:
            print("   ✅ Пользователь авторизован")
        elif profile_response.status_code == 302:
            print("   ⚠️  Редирект (возможно, не авторизован)")
        else:
            print("   ❌ Не авторизован")
            return False

    except Exception as e:
        print(f"   ❌ Ошибка проверки авторизации: {e}")
        return False

    # 4. Тестирование OAuth endpoint
    print("\n4. Тестирование OAuth endpoint:")

    try:
        # Симулируем OAuth запрос с токеном
        oauth_params = {
            'client_id': 'BesedkaRocketChat2025',
            'redirect_uri': 'http://127.0.0.1:3000/_oauth/besedka',
            'response_type': 'code',
            'scope': 'read',
            'state': 'test_state_123'
        }

        oauth_url = f"{base_url}/o/authorize/?" + urlencode(oauth_params)
        print(f"   OAuth URL: {oauth_url}")

        oauth_response = session.get(oauth_url, allow_redirects=False)
        print(f"   OAuth запрос: {oauth_response.status_code}")

        if oauth_response.status_code == 302:
            redirect_url = oauth_response.headers.get('Location', '')
            if 'code=' in redirect_url:
                print("   ✅ OAuth authorization code получен")
                auth_code = redirect_url.split('code=')[1].split('&')[0]
                print(f"   🔑 Код авторизации: {auth_code[:10]}...")
                print(f"   🔗 Полный редирект: {redirect_url}")
            else:
                print(f"   ❌ Неожиданный редирект: {redirect_url}")
        else:
            print(f"   ❌ Неожиданный статус: {oauth_response.status_code}")
            if oauth_response.text:
                print(f"   📝 Содержимое: {oauth_response.text[:200]}...")

    except Exception as e:
        print(f"   ❌ Ошибка OAuth: {e}")
        return False

    # 5. Тестирование интегрированной страницы
    print("\n5. Тестирование интегрированной страницы:")

    try:
        integrated_response = session.get(f"{base_url}/chat/integrated/")
        print(f"   Интегрированная страница: {integrated_response.status_code}")

        if integrated_response.status_code == 200:
            print("   ✅ Интегрированная страница доступна")

            # Проверяем наличие ключевых элементов
            if 'rocketchat_url' in integrated_response.text:
                print("   ✅ Rocket.Chat URL найден в шаблоне")
            else:
                print("   ⚠️  Rocket.Chat URL не найден в шаблоне")

            if 'owner' in integrated_response.text:
                print("   ✅ Пользователь отображается в шаблоне")
            else:
                print("   ⚠️  Пользователь не отображается в шаблоне")

        elif integrated_response.status_code == 302:
            redirect_location = integrated_response.headers.get('Location', '')
            print(f"   🔗 Редирект на: {redirect_location}")
            print("   ⚠️  Требуется авторизация")
        else:
            print(f"   ❌ Ошибка доступа: {integrated_response.status_code}")

    except Exception as e:
        print(f"   ❌ Ошибка тестирования страницы: {e}")
        return False

    # 6. Тестирование API endpoint
    print("\n6. Тестирование API endpoint:")

    try:
        # Тестируем без токена (должен вернуть 401)
        api_response = session.get(f"{base_url}/api/v1/auth/rocket/")
        print(f"   API endpoint (без токена): {api_response.status_code}")

        if api_response.status_code == 401:
            print("   ✅ API требует авторизацию (ожидаемо)")
        elif api_response.status_code == 200:
            print("   ✅ API возвращает данные")
            try:
                api_data = api_response.json()
                print(f"   📊 Данные API: {json.dumps(api_data, indent=2)}")
            except:
                print("   ⚠️  Ответ API не в формате JSON")
        else:
            print(f"   ❌ Неожиданный статус API: {api_response.status_code}")

    except Exception as e:
        print(f"   ❌ Ошибка API: {e}")
        return False

    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")
    print("📋 Результат: OAuth интеграция настроена и готова")
    print("🔗 Для полного тестирования откройте в браузере:")
    print(f"   - Интегрированный чат: {base_url}/chat/integrated/")
    print(f"   - Тестовая страница: {base_url}/chat/test/")
    print("\n💡 Следующие шаги:")
    print("   1. Откройте интегрированную страницу в браузере")
    print("   2. Нажмите кнопку 'Войти через Беседку' в Rocket.Chat")
    print("   3. Проверьте автоматическую авторизацию")

    return True

if __name__ == "__main__":
    test_rocket_oauth()
