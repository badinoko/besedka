from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import UserProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates or updates test users with predefined roles and credentials.'

    def handle(self, *args, **options):
        users_data = [
            {'username': 'owner_user', 'password': 'password123', 'email': 'owner@example.com', 'role': User.Role.OWNER, 'is_staff': True, 'is_superuser': True},
            {'username': 'moderator_user', 'password': 'password123', 'email': 'moderator@example.com', 'role': User.Role.ADMIN, 'is_staff': True},
            {'username': 'storeowner_user', 'password': 'password123', 'email': 'storeowner@example.com', 'role': User.Role.STORE_OWNER, 'is_staff': True},
            {'username': 'storeadmin_user', 'password': 'password123', 'email': 'storeadmin@example.com', 'role': User.Role.STORE_ADMIN, 'is_staff': True},
            {'username': 'regular_user', 'password': 'password123', 'email': 'user@example.com', 'role': User.Role.USER},
        ]

        self.stdout.write(self.style.SUCCESS('Initializing test users...'))

        for data in users_data:
            try:
                user, created = User.objects.get_or_create(
                    username=data['username'],
                    defaults={
                        'email': data['email'],
                        'role': data['role'],
                        'is_staff': data.get('is_staff', False),
                        'is_superuser': data.get('is_superuser', False)
                    }
                )

                if created:
                    user.set_password(data['password'])
                    user.save()
                    UserProfile.objects.get_or_create(user=user) # Ensure profile exists
                    self.stdout.write(self.style.SUCCESS(f"User {data['username']} created with role {data['role']}."))
                else:
                    # Update existing user details if needed, but be careful with password
                    user.email = data['email'] # Keep email updated
                    user.role = data['role']
                    user.is_staff = data.get('is_staff', False)
                    user.is_superuser = data.get('is_superuser', False)
                    # Optionally, uncomment to reset password on existing test users:
                    user.set_password(data['password'])
                    user.save()
                    UserProfile.objects.get_or_create(user=user) # Ensure profile exists
                    self.stdout.write(self.style.WARNING(f"User {data['username']} already exists. Email, role, staff status, and password updated."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing user {data['username']}: {e}"))

        self.stdout.write(self.style.SUCCESS('Test users initialization complete.'))
