from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminPagesSmokeTest(TestCase):
    """Быстрые smoke-тесты для кастомных административных панелей."""

    fixtures = []

    def setUp(self):
        self.client = Client()
        # Создаем пользователя-владельца платформы для тестов
        self.owner_user = User.objects.create_user(
            username="test_owner",
            email="test_owner@besedka.com",
            password="test_pass",
            role="owner",
            is_staff=True,
            is_active=True
        )
        # Авторизация созданным владельцем платформы
        self.client.login(username="test_owner", password="test_pass")

    def _assert_status_200(self, url: str, name: str):
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            200,
            msg=f"{name} должна отвечать HTTP 200, получено {response.status_code}",
        )
        return response

    def test_owner_admin_index(self):
        """Панель владельца платформы отвечает 200 и не содержит старый sidebar."""
        response = self._assert_status_200("/owner_admin/", "Owner admin index")
        # Проверяем что CSS скрывает nav-sidebar (display: none !important)
        content = response.content.decode()
        self.assertIn("display: none !important", content, "CSS должен содержать скрытие sidebar")
        self.assertIn(".nav-sidebar", content, "CSS правила для скрытия nav-sidebar должны быть")

    def test_manage_store_owner_view(self):
        """Страница управления владельцем магазина открывается корректно."""
        self._assert_status_200(reverse("owner_admin:manage_store_owner"), "Manage store owner")

    def test_moderator_admin_index(self):
        """Админка модератора открывается для owner (имеет права)."""
        self._assert_status_200("/moderator_admin/", "Moderator admin index")

    def test_store_owner_admin_index(self):
        """Админка владельца магазина не должна быть доступна владельцу платформы."""
        response = self.client.get("/store_owner/")
        self.assertIn(response.status_code, [302, 403], msg="Owner не должен заходить в store_owner admin")
