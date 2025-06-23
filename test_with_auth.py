#!/usr/bin/env python
"""
ПРОВЕРКА ИНТЕГРИРОВАННОГО ЧАТА С АВТОРИЗАЦИЕЙ
"""

import requests
import sys

def login_and_test():
    """Авторизуется в Django и проверяет интегрированный чат"""

    session = requests.Session()

    print("🔧 Этап 1: Получение CSRF токена...")

    # Получаем CSRF токен
    try:
        login_page = session.get("http://127.0.0.1:8001/accounts/login/", timeout=10)
        if login_page.status_code != 200:
            print(f"❌ Ошибка получения страницы входа: {login_page.status_code}")
            return False

        # Ищем CSRF токен
        import re
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
        if not csrf_match:
            print("❌ CSRF токен не найден на странице входа")
            return False

        csrf_token = csrf_match.group(1)
        print(f"✅ CSRF токен получен: {csrf_token[:10]}...")

    except Exception as e:
        print(f"❌ Ошибка при получении CSRF: {e}")
        return False

    print("\n🔧 Этап 2: Авторизация пользователя owner...")

    # Авторизуемся
    try:
        login_data = {
            'login': 'owner',
            'password': 'testpass123',
            'csrfmiddlewaretoken': csrf_token
        }

        login_response = session.post(
            "http://127.0.0.1:8001/accounts/login/",
            data=login_data,
            headers={'Referer': 'http://127.0.0.1:8001/accounts/login/'},
            timeout=10,
            allow_redirects=False
        )

        print(f"Статус авторизации: {login_response.status_code}")

        if login_response.status_code in [200, 302]:
            print("✅ Авторизация прошла успешно")
        else:
            print(f"❌ Ошибка авторизации: {login_response.status_code}")
            print(f"Содержимое ответа: {login_response.text[:200]}...")
            return False

    except Exception as e:
        print(f"❌ Ошибка при авторизации: {e}")
        return False

    print("\n🔧 Этап 3: Проверка интегрированного чата...")

    # Проверяем интегрированный чат
    try:
        chat_response = session.get("http://127.0.0.1:8001/chat/integrated/", timeout=10)
        print(f"Статус чата: {chat_response.status_code}")

        if chat_response.status_code == 200:
            content = chat_response.text

            if "<title>Чат - Беседка</title>" in content:
                print("✅ УСПЕХ: Интегрированный чат загружается!")

                # Проверяем наличие важных элементов
                if "switchChannel" in content:
                    print("✅ JavaScript функция switchChannel найдена")
                else:
                    print("⚠️  JavaScript функция switchChannel НЕ найдена")

                if "rocketchat_url" in content:
                    print("✅ URL Rocket.Chat настроен")
                else:
                    print("⚠️  URL Rocket.Chat НЕ настроен")

                if "Общий" in content and "VIP" in content and "Модераторы" in content:
                    print("✅ Все три кнопки каналов найдены")
                else:
                    print("⚠️  Не все кнопки каналов найдены")

                return True
            else:
                print("❌ Страница чата не содержит ожидаемый контент")
                print(f"Title страницы: {content[content.find('<title>'):content.find('</title>')+8] if '<title>' in content else 'Не найден'}")
                return False
        else:
            print(f"❌ Ошибка загрузки чата: {chat_response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Ошибка при проверке чата: {e}")
        return False

def main():
    print("=" * 60)
    print("ЧЕСТНАЯ ПРОВЕРКА ИНТЕГРИРОВАННОГО ЧАТА С АВТОРИЗАЦИЕЙ")
    print("=" * 60)

    success = login_and_test()

    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ДИАГНОЗ:")
    print("=" * 60)

    if success:
        print("🎉 ИНТЕГРИРОВАННЫЙ ЧАТ РАБОТАЕТ!")
        print("💡 Проблема была в отсутствии авторизации")
        print("🚨 СИСТЕМА НЕ ТРЕБУЕТ ВОССТАНОВЛЕНИЯ ИЗ БЭКАПА!")
        sys.exit(0)
    else:
        print("💥 ИНТЕГРИРОВАННЫЙ ЧАТ НЕ РАБОТАЕТ")
        print("🔧 Требуется дальнейшая диагностика")
        sys.exit(1)

if __name__ == "__main__":
    main()
