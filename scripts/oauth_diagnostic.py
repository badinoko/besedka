#!/usr/bin/env python3
"""
Диагностика и исправление OAuth настроек для Rocket.Chat
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from oauth2_provider.models import Application

def main():
    print("🔍 ДИАГНОСТИКА OAUTH НАСТРОЕК ДЛЯ ROCKET.CHAT")
    print("=" * 50)

    # Получаем OAuth приложение
    app = Application.objects.filter(client_id="BesedkaRocketChat2025").first()

    if not app:
        print("❌ OAuth приложение не найдено!")
        print("🔧 Создаю новое приложение...")

        app = Application.objects.create(
            name="RocketChat Besedka",
            client_id="BesedkaRocketChat2025",
            client_secret="SecureSecretKey2025BesedkaRocketChatSSO",
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris="http://127.0.0.1:3000/_oauth/besedka"
        )
        print("✅ OAuth приложение создано!")

    print("\n📊 ТЕКУЩИЕ НАСТРОЙКИ OAUTH:")
    print(f"Name: {app.name}")
    print(f"Client ID: {app.client_id}")
    print(f"Client Secret: {app.client_secret}")
    print(f"Client Type: {app.client_type}")
    print(f"Grant Type: {app.authorization_grant_type}")
    print(f"Redirect URIs: {app.redirect_uris}")
    print(f"Skip Authorization: {app.skip_authorization}")

    # Проверяем redirect_uri
    correct_redirect = "http://127.0.0.1:3000/_oauth/besedka"

    if app.redirect_uris != correct_redirect:
        print(f"\n⚠️ ПРОБЛЕМА: Неправильный redirect_uri!")
        print(f"Текущий: {app.redirect_uris}")
        print(f"Нужный: {correct_redirect}")

        # Исправляем
        app.redirect_uris = correct_redirect
        app.skip_authorization = True  # Автоматическое одобрение
        app.save()

        print("✅ Redirect URI исправлен!")
    else:
        print("✅ Redirect URI корректный!")

    # Проверяем skip_authorization
    if not app.skip_authorization:
        print("\n⚠️ ПРОБЛЕМА: Skip Authorization отключено!")
        app.skip_authorization = True
        app.save()
        print("✅ Skip Authorization включено!")
    else:
        print("✅ Skip Authorization включено!")

    print("\n🔗 ССЫЛКИ ДЛЯ ТЕСТИРОВАНИЯ:")
    print(f"Django OAuth: http://127.0.0.1:8001/o/authorize/?client_id={app.client_id}&redirect_uri={correct_redirect}&response_type=code&scope=rocketchat")
    print(f"Rocket.Chat: http://127.0.0.1:3000/")
    print(f"Тестовая страница: http://127.0.0.1:8001/chat/test/")

    print("\n✅ ДИАГНОСТИКА ЗАВЕРШЕНА!")
    print("📋 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Убедитесь, что в Rocket.Chat настроен Custom OAuth 'besedka'")
    print("2. Проверьте, что кнопка 'Sign in with Besedka' использует правильные настройки")
    print("3. Протестируйте OAuth flow в браузере")

if __name__ == "__main__":
    main()
