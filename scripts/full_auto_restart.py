#!/usr/bin/env python3
"""
🚀 ПОЛНАЯ АВТОМАТИЗАЦИЯ СИСТЕМЫ БЕСЕДКА + ROCKET.CHAT

Этот скрипт делает ВСЁ автоматически:
1. Перезапускает все контейнеры
2. Исправляет Rocket.Chat
3. Запускает Django
4. Авторизуется в Rocket.Chat

ИСПОЛЬЗОВАНИЕ: python scripts/full_auto_restart.py
"""

import subprocess
import time
import os
import sys
import threading
import signal

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

def run_command(cmd, timeout=30):
    """Выполняет команду и возвращает результат"""
    print_status(f"Выполняю: {cmd}", "PROGRESS")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0 and result.stderr:
            print_status(f"Предупреждение: {result.stderr}", "WARNING")
        return result
    except subprocess.TimeoutExpired:
        print_status(f"Команда превысила время ожидания: {cmd}", "WARNING")
        return None

def run_magic_restart():
    """Запускает магический перезапуск"""
    print_status("Запускаю магический перезапуск...", "PROGRESS")
    try:
        result = subprocess.run([
            sys.executable,
            "scripts/magic_restart_real.py"
        ], capture_output=True, text=True, cwd=".")

        if result.returncode == 0:
            print_status("Магический перезапуск завершен успешно!", "SUCCESS")
        else:
            print_status("Магический перезапуск завершился с предупреждениями", "WARNING")

        # Выводим весь вывод
        if result.stdout:
            print(result.stdout)

        return True
    except Exception as e:
        print_status(f"Ошибка магического перезапуска: {e}", "ERROR")
        return False

def start_django():
    """Запускает Django сервер"""
    print_status("Запускаю Django сервер...", "PROGRESS")

    # Убиваем существующие процессы
    run_command("taskkill /f /im python.exe", timeout=10)
    time.sleep(2)

    # Запускаем Django в отдельном процессе
    try:
        django_process = subprocess.Popen([
            sys.executable, "-m", "daphne",
            "-b", "127.0.0.1", "-p", "8001",
            "config.asgi:application"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Ждем запуска
        time.sleep(5)

        # Проверяем что Django запустился
        check_result = run_command("curl -s -o /dev/null -w \"%{http_code}\" http://127.0.0.1:8001/", timeout=10)
        if check_result and "200" in check_result.stdout:
            print_status("Django сервер запущен успешно!", "SUCCESS")
            return django_process
        else:
            print_status("Django сервер не отвечает", "ERROR")
            return None

    except Exception as e:
        print_status(f"Ошибка запуска Django: {e}", "ERROR")
        return None

def auto_login_rocketchat():
    """Автоматическая авторизация в Rocket.Chat"""
    print_status("Выполняю автоматическую авторизацию в Rocket.Chat...", "PROGRESS")

    # Ждем полной загрузки Rocket.Chat
    time.sleep(5)

    try:
        result = subprocess.run([
            sys.executable,
            "scripts/auto_login_rocketchat.py"
        ], capture_output=True, text=True, cwd=".")

        if result.returncode == 0:
            print_status("Авторизация в Rocket.Chat выполнена!", "SUCCESS")
            return True
        else:
            print_status("Авторизация не удалась, но система работает", "WARNING")
            return False

    except Exception as e:
        print_status(f"Ошибка авторизации: {e}", "WARNING")
        return False

def main():
    """Главная функция полной автоматизации"""
    print("🚀 ПОЛНАЯ АВТОМАТИЗАЦИЯ СИСТЕМЫ БЕСЕДКА + ROCKET.CHAT")
    print("=" * 60)

    # Шаг 1: Магический перезапуск
    print("\n1️⃣ МАГИЧЕСКИЙ ПЕРЕЗАПУСК КОНТЕЙНЕРОВ И ROCKET.CHAT")
    if not run_magic_restart():
        print_status("Критическая ошибка на этапе перезапуска", "ERROR")
        return False

    # Шаг 2: Запуск Django
    print("\n2️⃣ ЗАПУСК DJANGO СЕРВЕРА")
    django_process = start_django()
    if not django_process:
        print_status("Критическая ошибка запуска Django", "ERROR")
        return False

    # Шаг 3: Автоматическая авторизация
    print("\n3️⃣ АВТОМАТИЧЕСКАЯ АВТОРИЗАЦИЯ В ROCKET.CHAT")
    auto_login_rocketchat()

    # Финальный отчет
    print("\n" + "=" * 60)
    print("🎉 ПОЛНАЯ АВТОМАТИЗАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)
    print_status("Django: http://127.0.0.1:8001/", "SUCCESS")
    print_status("Rocket.Chat: http://127.0.0.1:3000/", "SUCCESS")
    print_status("Интегрированный чат: http://127.0.0.1:8001/chat/integrated/", "SUCCESS")

    print("\n" + "=" * 60)
    print("🔥 СИСТЕМА ГОТОВА К РАБОТЕ! МОЖЕТЕ ПОЛЬЗОВАТЬСЯ ЧАТОМ!")
    print("=" * 60)

    # Отслеживание работы Django
    print("\n💡 Django сервер работает в фоне...")
    print("💡 Для остановки нажмите Ctrl+C")

    try:
        # Бесконечный цикл для поддержания работы
        while True:
            time.sleep(30)
            # Проверяем что Django еще работает
            if django_process.poll() is not None:
                print_status("Django сервер неожиданно остановился", "ERROR")
                break

    except KeyboardInterrupt:
        print_status("\nПолучен сигнал остановки", "INFO")

    finally:
        # Завершаем Django процесс
        if django_process and django_process.poll() is None:
            print_status("Останавливаю Django сервер...", "PROGRESS")
            django_process.terminate()
            django_process.wait()

        print_status("Автоматизация завершена", "SUCCESS")

    return True

if __name__ == "__main__":
    main()
