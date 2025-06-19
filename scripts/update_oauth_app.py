import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from oauth2_provider.models import Application
from django.contrib.auth import get_user_model

User = get_user_model()

# Обновляем OAuth приложение
try:
    app = Application.objects.get(client_id='BesedkaRocketChat2025')
    app.skip_authorization = True
    app.save()
    print(f"✅ OAuth приложение обновлено:")
    print(f"   - Client ID: {app.client_id}")
    print(f"   - Skip authorization: {app.skip_authorization}")
    print(f"   - Redirect URI: {app.redirect_uris}")
except Application.DoesNotExist:
    print("❌ OAuth приложение BesedkaRocketChat2025 не найдено!")

    # Создаем новое приложение
    try:
        owner = User.objects.get(username='owner')
        app = Application.objects.create(
            user=owner,
            name='Rocket.Chat OAuth',
            client_id='BesedkaRocketChat2025',
            client_secret='rocketchat_secret_2025',
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            redirect_uris='http://127.0.0.1:3000/_oauth/besedka',
            skip_authorization=True  # Автоматически одобрять запросы
        )
        print(f"✅ OAuth приложение создано:")
        print(f"   - Client ID: {app.client_id}")
        print(f"   - Client Secret: {app.client_secret}")
        print(f"   - Skip authorization: {app.skip_authorization}")
    except User.DoesNotExist:
        print("❌ Пользователь 'owner' не найден!")
