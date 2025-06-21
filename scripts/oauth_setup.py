from oauth2_provider.models import Application
Application.objects.filter(name="RocketChat Besedka").delete()
app = Application.objects.create(name="RocketChat Besedka", client_id="BesedkaRocketChat2025", client_secret="SecureSecretKey2025BesedkaRocketChatSSO", client_type=Application.CLIENT_CONFIDENTIAL, authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE)
