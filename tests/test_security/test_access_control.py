from django.test import TestCase, Client
from django.urls import reverse, reverse_lazy
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class AccessControlTest(TestCase):
    """Тесты разделения доступа к административным интерфейсам."""

    @classmethod
    def setUpTestData(cls):
        # Создаем пользователей всех ролей
        cls.platform_owner = User.objects.create_user(
            username='platform_owner', password='password123', role='owner', is_staff=True, email='owner@example.com'
        )
        cls.store_owner_user = User.objects.create_user(
            username='store_owner_user', password='password123', role='store_owner', is_staff=True, email='storeowner@example.com'
        )
        cls.moderator_user = User.objects.create_user(
            username='moderator_user', password='password123', role='admin', is_staff=True, email='moderator@example.com'
        )
        cls.store_admin_user = User.objects.create_user(
            username='store_admin_user', password='password123', role='store_admin', is_staff=True, email='storeadmin@example.com'
        )
        cls.regular_user = User.objects.create_user(
            username='regular_user', password='password123', role='user', email='user@example.com'
        )

        cls.owner_admin_url = '/owner_admin/'
        cls.moderator_admin_url = '/moderator_admin/'
        cls.store_owner_admin_url = '/store_owner/'
        cls.store_admin_url = '/store_admin_site/'
        cls.django_admin_url = '/admin/'


    def test_platform_owner_access(self):
        """Тесты доступа для Владельца Платформы."""
        self.client.login(username='platform_owner', password='password123')

        response = self.client.get(self.owner_admin_url)
        self.assertEqual(response.status_code, 200, "Owner должен иметь доступ к своей админке")

        response = self.client.get(self.moderator_admin_url)
        self.assertEqual(response.status_code, 200, "Owner должен иметь доступ к админке модераторов")

        response = self.client.get(self.store_owner_admin_url)
        self.assertEqual(response.status_code, 302, "Owner НЕ должен иметь доступ к админке владельца магазина")
        self.assertIn('/login/', response['Location'], "Должно быть перенаправление на логин")

        response = self.client.get(self.store_admin_url)
        self.assertEqual(response.status_code, 302, "Owner НЕ должен иметь доступ к админке администратора магазина")
        self.assertIn('/login/', response['Location'], "Должно быть перенаправление на логин")

    def test_store_owner_access(self):
        """Тесты доступа для Владельца Магазина."""
        self.client.login(username='store_owner_user', password='password123')

        response = self.client.get(self.store_owner_admin_url)
        self.assertEqual(response.status_code, 200, "Store Owner должен иметь доступ к своей админке")

        response = self.client.get(self.store_admin_url)
        self.assertEqual(response.status_code, 200, "Store Owner должен иметь доступ к админке администратора магазина")

        response = self.client.get(self.owner_admin_url)
        self.assertEqual(response.status_code, 302, "Store Owner НЕ должен иметь доступ к админке владельца платформы")
        self.assertIn('/login/', response['Location'], "Должно быть перенаправление на логин")

        response = self.client.get(self.moderator_admin_url)
        self.assertEqual(response.status_code, 302, "Store Owner НЕ должен иметь доступ к админке модераторов")
        self.assertIn('/login/', response['Location'], "Должно быть перенаправление на логин")

    def test_moderator_access(self):
        """Тесты доступа для Модератора Платформы."""
        self.client.login(username='moderator_user', password='password123')

        response = self.client.get(self.moderator_admin_url)
        self.assertEqual(response.status_code, 200, "Moderator должен иметь доступ к своей админке")

        response = self.client.get(self.owner_admin_url)
        self.assertEqual(response.status_code, 302, "Moderator НЕ должен иметь доступ к админке владельца платформы")
        self.assertIn('/login/', response['Location'], "Должно быть перенаправление на логин")

        response = self.client.get(self.store_owner_admin_url)
        self.assertEqual(response.status_code, 302, "Moderator НЕ должен иметь доступ к админке владельца магазина")
        self.assertIn('/login/', response['Location'], "Должно быть перенаправление на логин")

        response = self.client.get(self.store_admin_url)
        self.assertEqual(response.status_code, 302, "Moderator НЕ должен иметь доступ к админке администратора магазина")
        self.assertIn('/login/', response['Location'], "Должно быть перенаправление на логин")


    def test_store_admin_access(self):
        """Тесты доступа для Администратора Магазина."""
        self.client.login(username='store_admin_user', password='password123')

        response = self.client.get(self.store_admin_url)
        self.assertEqual(response.status_code, 200, "Store Admin должен иметь доступ к своей админке")

        response = self.client.get(self.store_owner_admin_url)
        self.assertEqual(response.status_code, 302, "Store Admin НЕ должен иметь доступ к админке владельца магазина")
        self.assertIn('/login/', response['Location'], "Должно быть перенаправление на логин")

        response = self.client.get(self.owner_admin_url)
        self.assertEqual(response.status_code, 302, "Store Admin НЕ должен иметь доступ к админке владельца платформы")
        self.assertIn('/login/', response['Location'], "Должно быть перенаправление на логин")

        response = self.client.get(self.moderator_admin_url)
        self.assertEqual(response.status_code, 302, "Store Admin НЕ должен иметь доступ к админке модераторов")
        self.assertIn('/login/', response['Location'], "Должно быть перенаправление на логин")

    def test_regular_user_no_admin_access(self):
        """Обычный пользователь не должен иметь доступ к админкам."""
        self.client.login(username='regular_user', password='password123')

        admin_urls = [
            self.owner_admin_url,
            self.moderator_admin_url,
            self.store_owner_admin_url,
            self.store_admin_url,
            self.django_admin_url
        ]
        for url in admin_urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [302, 403, 404], f"Regular user не должен иметь доступ к {url}")


    def test_anonymous_user_redirected_to_login(self):
        """Анонимный пользователь должен перенаправляться на страницу входа."""
        admin_url_map = {
            self.owner_admin_url: f"{self.owner_admin_url}login/",
            self.moderator_admin_url: f"{self.moderator_admin_url}login/",
            self.store_owner_admin_url: f"{self.store_owner_admin_url}login/",
            self.store_admin_url: f"{self.store_admin_url}login/",
            # Для стандартной Django админки ожидаем редирект на глобальный LOGIN_URL
            self.django_admin_url: f"{reverse(settings.LOGIN_URL)}",
        }

        for url, expected_login_base in admin_url_map.items():
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302,
                             f"Должен быть редирект (302) с {url} для анонимного пользователя.")
            actual_redirect_location = response['Location']

            # Для стандартной Django админки добавляем ?next=
            if url == self.django_admin_url:
                 expected_redirect_url_with_next = f"{expected_login_base}?next={url}"
            else:
                 expected_redirect_url_with_next = f"{expected_login_base}?next={url}"


            self.assertEqual(actual_redirect_location, expected_redirect_url_with_next,
                             f"Редирект с {url} ({actual_redirect_location}) должен вести на {expected_redirect_url_with_next}")
