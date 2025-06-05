from django.core.management.base import BaseCommand
from django.test.client import Client
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Test growlogs functionality'

    def handle(self, *args, **options):
        User = get_user_model()
        client = Client()

        self.stdout.write("🔍 Тестирование гроу-репортов...")

        # Тестируем без авторизации
        self.stdout.write("\n1. Тест без авторизации:")

        tests = [
            ('Список гроу-репортов', '/growlogs/'),
            ('Детали гроу-репорта 1', '/growlogs/1/'),
            ('Детали гроу-репорта 2', '/growlogs/2/'),
        ]

        for test_name, url in tests:
            try:
                response = client.get(url)
                if response.status_code == 200:
                    self.stdout.write(f"✅ {test_name}: OK ({response.status_code})")
                elif response.status_code == 404:
                    self.stdout.write(f"⚠️ {test_name}: Не найден ({response.status_code})")
                else:
                    self.stdout.write(f"❌ {test_name}: Ошибка ({response.status_code})")

            except Exception as e:
                self.stdout.write(f"❌ {test_name}: Исключение - {e}")

        # Тестируем с авторизацией
        self.stdout.write("\n2. Тест с авторизацией:")

        # Пытаемся найти пользователя
        test_users = ['regular_user', 'user', 'alice_grower', 'bob_botanist']
        user = None

        for username in test_users:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(f"✅ Найден пользователь: {username}")
                break
            except User.DoesNotExist:
                continue

        if not user:
            self.stdout.write("❌ Не найден ни один тестовый пользователь")
            return

        # Логинимся
        client.force_login(user)

        auth_tests = [
            ('Мои гроу-репорты', '/growlogs/my-logs/'),
            ('Создание гроу-репорта', '/growlogs/create/'),
        ]

        for test_name, url in auth_tests:
            try:
                response = client.get(url)
                if response.status_code == 200:
                    self.stdout.write(f"✅ {test_name}: OK ({response.status_code})")
                elif response.status_code == 302:
                    self.stdout.write(f"⚠️ {test_name}: Перенаправление ({response.status_code})")
                else:
                    self.stdout.write(f"❌ {test_name}: Ошибка ({response.status_code})")

            except Exception as e:
                self.stdout.write(f"❌ {test_name}: Исключение - {e}")

        self.stdout.write("\n📊 Тестирование завершено!")
