from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class UserCabinetAccessTest(TestCase):
    """Тесты доступа к личному кабинету /users/cabinet/"""

    @classmethod
    def setUpTestData(cls):
        cls.platform_owner = User.objects.create_user(username='platform_owner', password='password123', role='owner', email='owner@example.com')
        cls.store_owner_user = User.objects.create_user(username='store_owner_user', password='password123', role='store_owner', email='storeowner@example.com')
        cls.moderator_user = User.objects.create_user(username='moderator_user', password='password123', role='admin', email='moderator@example.com')
        cls.store_admin_user = User.objects.create_user(username='store_admin_user', password='password123', role='store_admin', email='storeadmin@example.com')
        cls.regular_user = User.objects.create_user(username='regular_user', password='password123', role='user', email='user@example.com')
        cls.cabinet_url = reverse('users:profile')

    def test_anonymous_user_redirected_to_login(self):
        """Анонимный пользователь перенаправляется на страницу входа."""
        response = self.client.get(self.cabinet_url)
        self.assertRedirects(response, f"{reverse('account_login')}?next={self.cabinet_url}")

    def _check_cabinet_access_and_links(self, username, expected_template, expected_personal_links, expected_admin_links):
        self.client.login(username=username, password='password123')
        response = self.client.get(self.cabinet_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, expected_template)

        # Проверяем наличие персональных ссылок
        for link_title in expected_personal_links:
            self.assertContains(response, link_title)

        # Проверяем наличие админских ссылок
        for link_title in expected_admin_links:
            self.assertContains(response, link_title)
        self.client.logout()

    def test_regular_user_cabinet(self):
        """Доступ и ссылки для обычного пользователя."""
        expected_personal = ['Мой профиль', 'Редактировать профиль', 'Сменить пароль']
        expected_admin = []
        self._check_cabinet_access_and_links(
            self.regular_user.username,
            'users/cabinet_user.html',
            expected_personal,
            expected_admin
        )

    def test_platform_owner_cabinet(self):
        """Доступ и ссылки для владельца платформы."""
        expected_personal = ['Управление профилем', 'Редактировать профиль', 'Сменить пароль']
        expected_admin = ['Панель владельца платформы']
        self._check_cabinet_access_and_links(
            self.platform_owner.username,
            'users/cabinet_owner.html',
            expected_personal,
            expected_admin
        )

    def test_moderator_cabinet(self):
        """Доступ и ссылки для модератора."""
        expected_personal = ['Управление профилем', 'Редактировать профиль', 'Сменить пароль']
        expected_admin = ['Панель модератора']
        self._check_cabinet_access_and_links(
            self.moderator_user.username,
            'users/cabinet_moderator.html',
            expected_personal,
            expected_admin
        )

    def test_store_owner_cabinet(self):
        """Доступ и ссылки для владельца магазина."""
        expected_personal = ['Управление профилем', 'Редактировать профиль', 'Сменить пароль']
        expected_admin = ['Панель владельца магазина']
        self._check_cabinet_access_and_links(
            self.store_owner_user.username,
            'users/cabinet_store_owner.html',
            expected_personal,
            expected_admin
        )

    def test_store_admin_cabinet(self):
        """Доступ и ссылки для администратора магазина."""
        expected_personal = ['Управление профилем', 'Редактировать профиль', 'Сменить пароль']
        expected_admin = ['Панель администратора магазина']
        self._check_cabinet_access_and_links(
            self.store_admin_user.username,
            'users/cabinet_store_admin.html',
            expected_personal,
            expected_admin
        )
