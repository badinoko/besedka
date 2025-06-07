from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import UserProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates unified test users with standard names and secure passwords.'

    def handle(self, *args, **options):
        users_data = [
            {
                'username': 'owner',
                'password': 'owner123secure',
                'email': 'owner@besedka.com',
                'role': User.Role.OWNER,
                'is_staff': True,
                'is_superuser': True,
                'name': 'Владелец Платформы'
            },
            {
                'username': 'admin',
                'password': 'admin123secure',
                'email': 'admin@besedka.com',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'name': 'Администратор Платформы'
            },
            {
                'username': 'store_owner',
                'password': 'store123secure',
                'email': 'store_owner@besedka.com',
                'role': User.Role.STORE_OWNER,
                'is_staff': True,
                'name': 'Владелец Магазина'
            },
            {
                'username': 'store_admin',
                'password': 'storeadmin123secure',
                'email': 'store_admin@besedka.com',
                'role': User.Role.STORE_ADMIN,
                'is_staff': True,
                'name': 'Администратор Магазина'
            },
            {
                'username': 'user',
                'password': 'user123secure',
                'email': 'user@besedka.com',
                'role': User.Role.USER,
                'name': 'Обычный Пользователь'
            },
        ]

        self.stdout.write(self.style.SUCCESS('🚀 Создание унифицированных пользователей...'))

        for data in users_data:
            try:
                user, created = User.objects.get_or_create(
                    username=data['username'],
                    defaults={
                        'email': data['email'],
                        'name': data['name'],
                        'role': data['role'],
                        'is_staff': data.get('is_staff', False),
                        'is_superuser': data.get('is_superuser', False)
                    }
                )

                if created:
                    user.set_password(data['password'])
                    user.save()
                    UserProfile.objects.get_or_create(user=user)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Пользователь {data['username']} создан с ролью {data['role']}"
                        )
                    )
                else:
                    # Обновляем существующего пользователя
                    user.email = data['email']
                    user.name = data['name']
                    user.role = data['role']
                    user.is_staff = data.get('is_staff', False)
                    user.is_superuser = data.get('is_superuser', False)
                    user.set_password(data['password'])  # Обновляем пароль
                    user.save()
                    UserProfile.objects.get_or_create(user=user)
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️ Пользователь {data['username']} уже существует. Данные обновлены."
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Ошибка при создании пользователя {data['username']}: {e}"
                    )
                )

        self.stdout.write(self.style.SUCCESS('✅ Унифицированные пользователи созданы!'))

        # Выводим итоговую информацию
        self.stdout.write('\n📊 СОЗДАННЫЕ ПОЛЬЗОВАТЕЛИ:')
        for data in users_data:
            self.stdout.write(f"👤 {data['username']} / {data['password']} - {data['role']}")
