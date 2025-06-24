from django.core.management.base import BaseCommand
from django.conf import settings
from oauth2_provider.models import Application


class Command(BaseCommand):
    """Management command to create or update the OAuth2 Application for Rocket.Chat SSO.

    This command is idempotent: it will create the application if it doesn't exist yet or
    update the existing one with FIXED credentials that match our Rocket.Chat setup scripts.
    After execution it prints the credentials so they can be copied to Rocket.Chat admin UI
    and to your .env file (as ROCKETCHAT_OAUTH_CLIENT_ID / _SECRET).
    """

    help = "Create or update OAuth2 Application for Rocket.Chat SSO and output its credentials."

    def handle(self, *args, **options):
        client_name = "Rocket.Chat"
        redirect_uri = settings.DOMAIN if hasattr(settings, "DOMAIN") else "http://127.0.0.1:3000"
        redirect_uri += "/_oauth/besedka"

        # ФИКСИРОВАННЫЕ УЧЕТНЫЕ ДАННЫЕ согласованные со скриптами
        fixed_client_id = "BesedkaRocketChat2025"
        fixed_client_secret = "SecureSecretKey2025BesedkaRocketChatSSO"

        # Создаем или обновляем приложение с фиксированными учетными данными
        app, created = Application.objects.update_or_create(
            client_id=fixed_client_id,  # Ищем по Client ID
            defaults={
                'name': client_name,
                'client_secret': fixed_client_secret,
                'client_type': Application.CLIENT_CONFIDENTIAL,
                'authorization_grant_type': Application.GRANT_AUTHORIZATION_CODE,
                'redirect_uris': redirect_uri,
            }
        )

        action = "CREATED" if created else "UPDATED"
        self.stdout.write(self.style.SUCCESS(f"[Rocket.Chat OAuth] {action} application with FIXED credentials ✔"))
        self.stdout.write(f"client_id: {app.client_id}")
        self.stdout.write(f"client_secret: {app.client_secret}")
        self.stdout.write(f"redirect_uri: {redirect_uri}")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("⚠️  ВАЖНО: Эти учетные данные синхронизированы со скриптами настройки Rocket.Chat"))
        self.stdout.write("🔧 Теперь OAuth между Django и Rocket.Chat будет работать правильно!")
