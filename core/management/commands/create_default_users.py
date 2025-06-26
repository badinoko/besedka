from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates the default users for the Besedka project as defined in BESEDKA_USER_SYSTEM.md'

    def handle(self, *args, **options):
        users_to_create = [
            {'username': 'owner', 'password': 'owner123secure', 'email': 'owner@besedka.com', 'role': 'owner', 'is_staff': True, 'is_superuser': True},
            {'username': 'admin', 'password': 'admin123secure', 'email': 'admin@besedka.com', 'role': 'moderator', 'is_staff': True, 'is_superuser': False},
            {'username': 'store_owner', 'password': 'storeowner123secure', 'email': 'store.owner@magicbeans.com', 'role': 'store_owner', 'is_staff': True, 'is_superuser': False},
            {'username': 'store_admin', 'password': 'storeadmin123secure', 'email': 'store.admin@magicbeans.com', 'role': 'store_admin', 'is_staff': True, 'is_superuser': False},
            {'username': 'test_user', 'password': 'user123secure', 'email': 'test.user@besedka.com', 'role': 'user', 'is_staff': False, 'is_superuser': False},
        ]

        for user_data in users_to_create:
            if not User.objects.filter(username=user_data['username']).exists():
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                user.role = user_data['role']
                user.is_staff = user_data['is_staff']
                user.is_superuser = user_data['is_superuser']
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Successfully created user: {user_data['username']}"))
            else:
                self.stdout.write(self.style.WARNING(f"User {user_data['username']} already exists. Skipping."))
