#!/usr/bin/env python
"""
ПОДРОБНАЯ ДИАГНОСТИКА ФОРМЫ ВХОДА
"""

import requests
import re

def debug_login_form():
    """Подробно исследует форму входа"""

    session = requests.Session()

    print("🔍 Получение страницы входа...")

    try:
        response = session.get("http://127.0.0.1:8001/accounts/login/")

        if response.status_code != 200:
            print(f"❌ Ошибка: {response.status_code}")
            return

        content = response.text
        print(f"✅ Страница получена, размер: {len(content)} символов")

        # Ищем форму
        form_match = re.search(r'<form[^>]*action="([^"]*)"[^>]*method="([^"]*)"[^>]*>(.*?)</form>', content, re.DOTALL | re.IGNORECASE)

        if not form_match:
            print("❌ Форма входа не найдена")
            return

        action = form_match.group(1)
        method = form_match.group(2)
        form_content = form_match.group(3)

        print(f"📝 Форма найдена:")
        print(f"   Action: {action}")
        print(f"   Method: {method}")

        # Ищем все поля input
        input_fields = re.findall(r'<input[^>]*name="([^"]*)"[^>]*(?:type="([^"]*)")?[^>]*>', form_content, re.IGNORECASE)

        print(f"\n🔧 Поля формы:")
        for name, input_type in input_fields:
            print(f"   {name}: {input_type or 'text'}")

        # Ищем CSRF токен
        csrf_match = re.search(r'name="csrfmiddlewaretoken"[^>]*value="([^"]*)"', content)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f"\n🔑 CSRF токен: {csrf_token[:20]}...")
        else:
            print("\n❌ CSRF токен не найден")
            return

        # Попробуем разные варианты авторизации
        test_variants = [
            {'login': 'owner', 'password': 'testpass123'},  # allauth обычно
            {'username': 'owner', 'password': 'testpass123'},  # стандартный Django
            {'email': 'owner@test.com', 'password': 'testpass123'},  # по email
        ]

        for i, variant in enumerate(test_variants, 1):
            print(f"\n🧪 Тестирую вариант {i}: {list(variant.keys())}")

            # Добавляем CSRF токен
            login_data = variant.copy()
            login_data['csrfmiddlewaretoken'] = csrf_token

            # Отправляем
            login_response = session.post(
                f"http://127.0.0.1:8001{action}" if action.startswith('/') else f"http://127.0.0.1:8001/accounts/login/",
                data=login_data,
                headers={'Referer': 'http://127.0.0.1:8001/accounts/login/'},
                timeout=10,
                allow_redirects=False
            )

            print(f"   Статус: {login_response.status_code}")

            if login_response.status_code == 302:
                redirect_url = login_response.headers.get('Location', 'не указан')
                print(f"   ✅ УСПЕХ! Редирект на: {redirect_url}")
                return True
            elif login_response.status_code == 200:
                print("   ⚠️  Возможно ошибка входа (остались на той же странице)")
                # Проверим на наличие ошибок
                if 'errorlist' in login_response.text.lower():
                    print("   💡 Найдены ошибки в форме")
            else:
                print(f"   ❌ Ошибка: {login_response.status_code}")

        return False

    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ДИАГНОСТИКА ФОРМЫ ВХОДА")
    print("=" * 60)

    success = debug_login_form()

    if success:
        print("\n🎉 АВТОРИЗАЦИЯ РАБОТАЕТ!")
    else:
        print("\n💥 АВТОРИЗАЦИЯ НЕ РАБОТАЕТ")
        print("Возможные причины:")
        print("- Неправильные учетные данные")
        print("- Проблемы с настройками allauth")
        print("- CSRF проблемы")
        print("- Другие настройки безопасности")
