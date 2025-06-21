from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='password123',
            email='testuser@example.com',
            role=User.Role.USER  # Обычный пользователь
        )
        self.client.login(username='testuser', password='password123')

    def test_profile_view_authenticated_user(self):
        """Тест: ProfileView доступен для аутентифицированного пользователя."""
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/cabinet_user.html')
        self.assertContains(response, 'Личный кабинет')
        self.assertEqual(response.context['user'], self.user)

    def test_profile_view_redirects_anonymous_user(self):
        """Тест: ProfileView перенаправляет анонимного пользователя на страницу входа."""
        self.client.logout()
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('account_login')}?next={reverse('users:profile')}")

    def test_profile_view_owner_template(self):
        """Тест: ProfileView использует правильный шаблон для владельца платформы."""
        owner_user = User.objects.create_user(
            username='testowner',
            password='password123',
            email='testowner@example.com',
            role=User.Role.OWNER
        )
        self.client.login(username='testowner', password='password123')
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/cabinet_owner.html')
        self.assertEqual(response.context['user'], owner_user)

    # Добавить аналогичные тесты для других ролей (admin, store_owner, store_admin)
    # для проверки использования Users/cabinet_moderator.html, users/cabinet_store_owner.html, users/cabinet_store_admin.html
