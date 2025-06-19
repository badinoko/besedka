from django.core.management.base import BaseCommand
from django.conf import settings
from oauth2_provider.models import Application


class Command(BaseCommand):
    """Management command to create or update the OAuth2 Application for Rocket.Chat SSO.

    This command is idempotent: it will create the application if it doesn't exist yet or
    update the existing one keeping the same client_id / client_secret when possible.
    After execution it prints the credentials so they can be copied to Rocket.Chat admin UI
    and to your .env file (as ROCKETCHAT_OAUTH_CLIENT_ID / _SECRET).
    """

    help = "Create or update OAuth2 Application for Rocket.Chat SSO and output its credentials."

    def handle(self, *args, **options):
        client_name = "Rocket.Chat"
        redirect_uri = settings.DOMAIN if hasattr(settings, "DOMAIN") else "http://127.0.0.1:3000"
        redirect_uri += "/_oauth/djangooauth2"

        app, created = Application.objects.update_or_create(
            name=client_name,
            defaults={
                "client_type": Application.CLIENT_CONFIDENTIAL,
                "authorization_grant_type": Application.GRANT_AUTHORIZATION_CODE,
                "redirect_uris": redirect_uri,
            },
        )

        action = "CREATED" if created else "UPDATED"
        self.stdout.write(self.style.SUCCESS(f"[Rocket.Chat OAuth] {action} application ✔"))
        self.stdout.write(f"client_id: {app.client_id}")
        self.stdout.write(f"client_secret: {app.client_secret}")
