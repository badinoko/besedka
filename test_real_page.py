#!/usr/bin/env python
"""
ЧЕСТНАЯ ПРОВЕРКА ИНТЕГРИРОВАННОГО ЧАТА
Без предрассудков, без предположений - только факты
"""

import requests
import sys
from urllib.parse import urljoin

def test_page(url, description):
    """Тестирует страницу и возвращает честный результат"""
    try:
        print(f"\n🔍 Проверяю {description}...")
        response = requests.get(url, timeout=10)

        print(f"HTTP статус: {response.status_code}")

        if response.status_code == 200:
            content = response.text[:500]  # Первые 500 символов

            # Проверяем на ошибки
            if "500 Internal Server Error" in content:
                print("❌ ОШИБКА: 500 Internal Server Error в содержимом")
                return False
            elif "404" in content and "Not Found" in content:
                print("❌ ОШИБКА: 404 Not Found в содержимом")
                return False
            elif "Подключение к чату" in content:
                print("✅ ХОРОШО: Страница чата загружается")
                return True
            elif "<title>Чат - Беседка</title>" in content:
                print("✅ ХОРОШО: Title страницы корректный")
                return True
            elif "Войти - Аккаунт" in content:
                print("🔄 РЕДИРЕКТ: Требуется авторизация")
                return "auth_required"
            elif "rocket.chat" in content.lower() or "meteor" in content.lower():
                print("✅ ХОРОШО: Rocket.Chat загружается")
                return True
            else:
                print("⚠️  НЕОПРЕДЕЛЕННО: Страница загружается, но контент не ясен")
                print(f"Начало содержимого: {content[:200]}...")
                return None
        else:
            print(f"❌ ОШИБКА: HTTP {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("❌ ОШИБКА: Таймаут соединения")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ ОШИБКА: Невозможно соединиться")
        return False
    except Exception as e:
        print(f"❌ ОШИБКА: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("ЧЕСТНАЯ ДИАГНОСТИКА СИСТЕМЫ ЧАТА")
    print("=" * 60)

    # Тестируем основные компоненты
    django_ok = test_page("http://127.0.0.1:8001/", "Django главная страница")
    rocketchat_ok = test_page("http://127.0.0.1:3000/", "Rocket.Chat главная страница")
    chat_integrated_ok = test_page("http://127.0.0.1:8001/chat/integrated/", "Интегрированный чат")

    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ДИАГНОЗ:")
    print("=" * 60)

    if chat_integrated_ok == "auth_required":
        print("🔑 ПРОБЛЕМА АВТОРИЗАЦИИ")
        print("Интегрированный чат требует авторизации в Django")
        print("РЕШЕНИЕ: Пользователь должен войти в систему через Django")
        sys.exit(4)
    elif django_ok and rocketchat_ok and chat_integrated_ok:
        print("🎉 ВСЁ РАБОТАЕТ! Система не требует восстановления!")
        print("🚨 НЕ ТРОГАЙ НИЧЕГО! Проблема может быть в браузере/кеше!")
        sys.exit(0)
    elif django_ok and rocketchat_ok and not chat_integrated_ok:
        print("🔧 ПРОБЛЕМА ТОЛЬКО В ИНТЕГРАЦИИ")
        print("Base сервисы работают, нужно исправить только Django view/template")
        sys.exit(1)
    elif not rocketchat_ok:
        print("💥 ПРОБЛЕМА В ROCKET.CHAT")
        print("Нужно восстановление из бэкапа")
        sys.exit(2)
    else:
        print("💀 КРИТИЧЕСКАЯ ОШИБКА")
        print("Проблемы в базовых сервисах")
        sys.exit(3)

if __name__ == "__main__":
    main()
