from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Checks access control for different user roles to admin interfaces.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Running Access Control Check..."))

        # Временно модифицируем ALLOWED_HOSTS
        original_allowed_hosts = list(settings.ALLOWED_HOSTS)
        if 'testserver' not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS.append('testserver')

        # Define roles and their test users (ensure these users exist or create them temporarily)
        # For simplicity, we assume users created in tests might not exist here,
        # so we'll rely on characteristics rather than specific usernames.
        roles_config = {
            'anonymous': {'login': False, 'is_staff': False, 'role': None},
            'regular_user': {'login': True, 'username': 'test_regular_user_access', 'password': 'password', 'is_staff': False, 'role': 'user'},
            'platform_owner': {'login': True, 'username': 'test_platform_owner_access', 'password': 'password', 'is_staff': True, 'role': 'owner'},
            'store_owner': {'login': True, 'username': 'test_store_owner_access', 'password': 'password', 'is_staff': True, 'role': 'store_owner'},
            'moderator': {'login': True, 'username': 'test_moderator_access', 'password': 'password', 'is_staff': True, 'role': 'admin'},
            'store_admin': {'login': True, 'username': 'test_store_admin_access', 'password': 'password', 'is_staff': True, 'role': 'store_admin'},
        }

        admin_urls_to_check = {
            'Django Admin (/admin/)': '/admin/',
            'Owner Admin (/owner_admin/)': '/owner_admin/',
            'Moderator Admin (/moderator_admin/)': '/moderator_admin/',
            'Store Owner Admin (/store_owner/)': '/store_owner/',
            'Store Admin (/store_admin/)': '/store_admin/',
            'User Management (StoreOwnerForm)': reverse('users:store_owner_management')
        }

        client = Client()

        for role_name, config in roles_config.items():
            self.stdout.write(self.style.HTTP_INFO(f"\n--- Checking Role: {role_name.upper()} ---"))

            user = None
            if config['login']:
                # Get or create a temporary user for the test
                try:
                    user = User.objects.get(username=config['username'])
                except User.DoesNotExist:
                    user_data = {k: v for k, v in config.items() if k in ['username', 'password', 'role', 'is_staff']}
                    if 'password' not in user_data: user_data['password'] = 'password' # default if missing
                    user = User.objects.create_user(**user_data)
                client.login(username=config['username'], password=config.get('password', 'password'))
            else:
                client.logout()

            for name, url in admin_urls_to_check.items():
                try:
                    response = client.get(url, HTTP_HOST='testserver')
                    status = response.status_code
                    redirect_location = response.get('Location', 'N/A') if status in [301, 302] else 'N/A'

                    if status == 200:
                        self.stdout.write(self.style.SUCCESS(f"  [ALLOWED] {name} (Status: {status})"))
                    elif status in [301, 302]:
                        self.stdout.write(self.style.WARNING(f"  [REDIRECT] {name} (Status: {status}) -> {redirect_location}"))
                    elif status == 403:
                        self.stdout.write(self.style.ERROR(f"  [FORBIDDEN] {name} (Status: {status})"))
                    elif status == 404:
                         self.stdout.write(self.style.ERROR(f"  [NOT FOUND] {name} (Status: {status})"))
                    else:
                        self.stdout.write(f"  [OTHER] {name} (Status: {status})")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  [ERROR] Accessing {name}: {e}"))

            # Clean up temporary user if created for this role check
            # if user and config['login'] and not User.objects.filter(username=config['username'], pk=user.pk).exists(): # Basic check if it was indeed a temp user
            #    user.delete() # Be cautious with auto-deleting users, ensure they are meant to be temporary

        # Восстанавливаем ALLOWED_HOSTS
        settings.ALLOWED_HOSTS = original_allowed_hosts

        self.stdout.write(self.style.SUCCESS("\nAccess Control Check Finished."))
