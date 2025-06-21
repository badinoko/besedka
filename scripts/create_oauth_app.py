import os
import sys
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.local'
import django
django.setup()

from oauth2_provider.models import Application
from django.contrib.auth import get_user_model

User = get_user_model()

# Получаем владельца
owner = User.objects.get(username='owner')

# Удаляем старое приложение если есть
Application.objects.filter(client_id='BesedkaRocketChat2025').delete()

# Создаем новое с помощью правильного метода
app = Application(
    client_id='BesedkaRocketChat2025',
    user=owner,
    redirect_uris='http://127.0.0.1:3000/_oauth/besedka',
    client_type=Application.CLIENT_CONFIDENTIAL,
    authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
    name='Besedka Rocket.Chat OAuth',
    skip_authorization=True
)

# Устанавливаем secret напрямую через метод
app.client_secret = Application.generate_client_secret()
app.save()

# Сохраняем незахешированный секрет
plain_secret = app.client_secret

print(f"OAuth Application Created:")
print(f"Client ID: {app.client_id}")
print(f"Client Secret: {plain_secret}")
print(f"Redirect URI: {app.redirect_uris}")
print(f"Skip Authorization: {app.skip_authorization}")

# Сохраняем в файл для удобства
with open('oauth_credentials.txt', 'w') as f:
    f.write(f"Client ID: {app.client_id}\n")
    f.write(f"Client Secret: {plain_secret}\n")
    f.write(f"Redirect URI: {app.redirect_uris}\n")

print("\nCredentials saved to oauth_credentials.txt")
