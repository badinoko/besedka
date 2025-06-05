from django.test import TestCase, Client
from django.urls import reverse
from users.models import User


class OwnerAccessTest(TestCase):
    """
    Тесты для проверки доступа владельца платформы ко всем админкам.
    """

    def setUp(self):
        """Настройка тестовых данных."""
        self.owner = User.objects.create_user(
            username='owner_test',
            email='owner@test.com',
            password='testpass123',
            role='owner',
            is_staff=True,
            is_superuser=True
        )
        self.client = Client()
        self.client.login(username='owner_test', password='testpass123')

    def test_owner_can_access_platform_admins(self):
        """Владелец должен иметь доступ к админкам платформы, но НЕ к админкам магазина."""
        # Админки платформы - разрешены
        allowed_urls = [
            '/owner_admin/',
            '/moderator_admin/',
        ]

        # Админки магазина - запрещены
        restricted_urls = [
            '/store_owner/',
            '/store_admin/',
        ]

        for url in allowed_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200,
                               f"Владелец должен иметь доступ к {url}")

        for url in restricted_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302,
                               f"Владелец НЕ должен иметь доступ к {url}")
                self.assertIn('/login/', response.url,
                            f"Владелец должен быть перенаправлен на логин с {url}")

    def test_owner_admin_redirect_from_base_admin(self):
        """Владелец должен перенаправляться в свою админку с /admin/."""
        response = self.client.get('/admin/')

        # Должен быть перенаправлен в админку владельца
        if response.status_code == 302:
            self.assertEqual(response.url, '/owner_admin/',
                           "Владелец не перенаправляется в свою админку с /admin/")

    def test_owner_access_without_redirect_loops(self):
        """Проверяем, что нет циклических перенаправлений для разрешенных админок."""
        # Только админки платформы - к ним у владельца есть доступ
        admin_urls = [
            '/owner_admin/',
            '/moderator_admin/',
        ]

        for url in admin_urls:
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)

                # Проверяем, что не более 5 перенаправлений (защита от циклов)
                self.assertLessEqual(len(response.redirect_chain), 5,
                                   f"Слишком много перенаправлений для {url}")

                # Финальный статус должен быть 200
                self.assertEqual(response.status_code, 200,
                               f"Финальный статус не 200 для {url}")


class AdminRoleRestrictionsTest(TestCase):
    """
    Тесты для проверки ограничений доступа других ролей.
    """

    def setUp(self):
        """Настройка тестовых данных."""
        # Модератор платформы
        self.admin = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_staff=True
        )

        # Владелец магазина
        self.store_owner = User.objects.create_user(
            username='store_owner_test',
            email='store_owner@test.com',
            password='testpass123',
            role='store_owner',
            is_staff=True
        )

        # Администратор магазина
        self.store_admin = User.objects.create_user(
            username='store_admin_test',
            email='store_admin@test.com',
            password='testpass123',
            role='store_admin',
            is_staff=True
        )

    def test_admin_restricted_from_store_and_owner_admins(self):
        """Модератор не должен иметь доступ к админкам магазина и владельца."""
        client = Client()
        client.login(username='admin_test', password='testpass123')

        restricted_urls = ['/store_owner/', '/store_admin/', '/owner_admin/']
        allowed_urls = ['/moderator_admin/']

        for url in restricted_urls:
            with self.subTest(url=url):
                response = client.get(url)
                # Должен быть перенаправлен (не 200)
                self.assertEqual(response.status_code, 302,
                               f"Модератор имеет доступ к {url}, но не должен")

        for url in allowed_urls:
            with self.subTest(url=url):
                response = client.get(url)
                # Должен иметь доступ
                self.assertIn(response.status_code, [200, 302])

    def test_store_owner_access_to_store_admins_only(self):
        """Владелец магазина должен иметь доступ только к админкам магазина."""
        client = Client()
        client.login(username='store_owner_test', password='testpass123')

        allowed_urls = ['/store_owner/', '/store_admin/']
        restricted_urls = ['/owner_admin/', '/moderator_admin/']

        for url in allowed_urls:
            with self.subTest(url=url):
                response = client.get(url)
                # Должен иметь доступ или быть перенаправлен в разрешенную админку
                self.assertIn(response.status_code, [200, 302])

        for url in restricted_urls:
            with self.subTest(url=url):
                response = client.get(url)
                # Должен быть перенаправлен (не иметь прямого доступа)
                self.assertEqual(response.status_code, 302,
                               f"Владелец магазина имеет доступ к {url}, но не должен")

    def test_store_admin_access_restricted(self):
        """Администратор магазина должен иметь доступ только к своей админке."""
        client = Client()
        client.login(username='store_admin_test', password='testpass123')

        allowed_urls = ['/store_admin/']
        restricted_urls = ['/owner_admin/', '/moderator_admin/', '/store_owner/']

        for url in allowed_urls:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertIn(response.status_code, [200, 302])

        for url in restricted_urls:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(response.status_code, 302,
                               f"Администратор магазина имеет доступ к {url}, но не должен")
