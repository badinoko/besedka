from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import UserProfile
from allauth.account.models import EmailAddress

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates or updates test users with predefined roles and credentials.'

    def handle(self, *args, **options):
        # Унифицированные пользователи согласно BESEDKA_USER_SYSTEM.md (SSOT)
        users_data = [
            {
                'username': 'owner',
                'password': 'owner123secure',
                'email': 'owner@besedka.com',
                'role': User.Role.OWNER,
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'admin',
                'password': 'admin123secure',
                'email': 'admin@besedka.com',
                'role': User.Role.MODERATOR,
                'is_staff': True,
            },
            {
                'username': 'store_owner',
                'password': 'storeowner123secure',
                'email': 'store.owner@magicbeans.com',
                'role': User.Role.STORE_OWNER,
                'is_staff': True,
            },
            {
                'username': 'store_admin',
                'password': 'storeadmin123secure',
                'email': 'store.admin@magicbeans.com',
                'role': User.Role.STORE_ADMIN,
                'is_staff': True,
            },
            {
                'username': 'test_user',
                'password': 'user123secure',
                'email': 'test.user@besedka.com',
                'role': User.Role.USER,
            },
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
                    # Создаём подтверждённый адрес электронной почты, чтобы Allauth не требовал верификации
                    EmailAddress.objects.update_or_create(
                        user=user,
                        email=data['email'],
                        defaults={
                            'primary': True,
                            'verified': True,
                        },
                    )
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
                    # Обновляем/создаём подтверждённый адрес электронной почты
                    EmailAddress.objects.update_or_create(
                        user=user,
                        email=data['email'],
                        defaults={
                            'primary': True,
                            'verified': True,
                        },
                    )
                    self.stdout.write(self.style.WARNING(f"User {data['username']} already exists. Email, role, staff status, and password updated."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing user {data['username']}: {e}"))

        self.stdout.write(self.style.SUCCESS('Test users initialization complete.'))
