#!/usr/bin/env python3
"""
🛡️ БЕЗОПАСНЫЙ ПЕРЕЗАПУСК БЕЗ ПОТЕРИ ДАННЫХ
Этот скрипт перезапускает сервисы БЕЗ удаления volumes
"""

import subprocess
import time
import requests

def run_command(cmd, description):
    """Выполнение команды с описанием"""
    print(f"🔄 {description}")
    print(f"   Команда: {cmd}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"   ✅ Успешно")
            if result.stdout.strip():
                print(f"   Вывод: {result.stdout.strip()}")
        else:
            print(f"   ⚠️ Код ошибки: {result.returncode}")
            if result.stderr.strip():
                print(f"   Ошибка: {result.stderr.strip()}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"   ⏳ Команда выполняется дольше 30 секунд...")
        return True
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False

def check_service(url, name, expected_code=200):
    """Проверка доступности сервиса"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_code:
            print(f"   ✅ {name}: HTTP {response.status_code} - работает")
            return True
        else:
            print(f"   ⚠️ {name}: HTTP {response.status_code} - проблемы")
            return False
    except Exception as e:
        print(f"   ❌ {name}: недоступен ({e})")
        return False

def safe_restart():
    """Безопасный перезапуск без потери данных"""
    print("🛡️ БЕЗОПАСНЫЙ ПЕРЕЗАПУСК СИСТЕМЫ")
    print("=" * 50)
    print("⚠️ ВАЖНО: Данные volumes НЕ БУДУТ удалены!")
    print("=" * 50)

    # Шаг 1: Остановка Python процессов
    run_command(
        "taskkill /f /im python.exe",
        "Остановка всех Python процессов"
    )

    # Шаг 2: Остановка web контейнера (НЕ УДАЛЯЯ volumes!)
    run_command(
        "docker-compose -f docker-compose.local.yml stop web",
        "Остановка web контейнера"
    )

    # Шаг 3: Перезапуск всех сервисов (БЕЗ удаления данных)
    print("\n🔄 Перезапуск Docker сервисов (данные сохраняются)...")
    run_command(
        "docker-compose -f docker-compose.local.yml up -d postgres redis mongo rocketchat",
        "Запуск основных сервисов"
    )

    # Шаг 4: Ожидание инициализации MongoDB
    print("\n⏳ Ожидание инициализации MongoDB...")
    time.sleep(10)

    # Шаг 5: Проверка статуса контейнеров
    print("\n📊 Проверка статуса контейнеров:")
    run_command(
        "docker ps --format \"table {{.Names}}\\t{{.Status}}\\t{{.Ports}}\"",
        "Текущий статус контейнеров"
    )

    # Шаг 6: Запуск Django через Daphne
    print("\n🚀 Запуск Django сервера...")
    print("   Команда: daphne -b 127.0.0.1 -p 8001 config.asgi:application")
    print("   ⚠️ ВЫПОЛНИТЕ ЭТУ КОМАНДУ ВРУЧНУЮ в отдельном терминале!")

    # Шаг 7: Ожидание и проверка сервисов
    print("\n⏳ Ожидание запуска сервисов (30 сек)...")
    time.sleep(30)

    print("\n🔍 Проверка доступности сервисов:")
    django_ok = check_service("http://127.0.0.1:8001", "Django")
    rocket_ok = check_service("http://127.0.0.1:3000", "Rocket.Chat")

    # Шаг 8: Результат
    print("\n" + "=" * 50)
    if django_ok and rocket_ok:
        print("🎉 ВСЕ СЕРВИСЫ РАБОТАЮТ!")
        print("✅ Django: http://127.0.0.1:8001")
        print("✅ Rocket.Chat: http://127.0.0.1:3000")
        print("🔄 Готов к запуску автоматической настройки:")
        print("   python scripts/auto_rocketchat.py")
    else:
        print("⚠️ НЕКОТОРЫЕ СЕРВИСЫ НЕ ОТВЕЧАЮТ")
        print("   Проверьте логи контейнеров:")
        print("   docker-compose -f docker-compose.local.yml logs rocketchat")

    print("=" * 50)

if __name__ == "__main__":
    try:
        safe_restart()
    except KeyboardInterrupt:
        print("\n⚠️ Перезапуск прерван пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
